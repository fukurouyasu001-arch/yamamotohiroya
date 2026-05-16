"""
キーワード辞書ベースの解析エンジン（現状方式）。
外部API不要。オフラインで動作する代わりに、文脈理解や否定形の検出は弱い。
LLM接続前のフォールバック・PoC用途として残す。
"""
import re
from app.models.candidate import TraitProfile, TextFeatures, TextAnalysisResult
from app.services.analyzer.base import AnalyzerEngine

# ──────────────────────────────────────────
# 特性スコア用キーワード辞書
# ──────────────────────────────────────────
_TRAIT_KEYWORDS: dict[str, list[tuple[str, float]]] = {
    "calm": [
        ("穏やか", 1.0), ("落ち着い", 1.0), ("安定", 0.8), ("温和", 0.9),
        ("丁寧", 0.7), ("ゆったり", 0.8), ("冷静", 0.9), ("沈着", 0.8),
        ("ペースを保", 0.7), ("焦らず", 0.8), ("動じない", 0.9),
    ],
    "empathy": [
        ("共感", 1.0), ("寄り添", 1.0), ("思いやり", 1.0), ("温かい", 0.9),
        ("優しい", 0.8), ("気持ちを理解", 0.9), ("傾聴", 0.9), ("受け止め", 0.8),
        ("気にかけ", 0.7), ("心に寄り添", 1.0), ("相手の立場", 0.8),
    ],
    "energy": [
        ("積極的", 1.0), ("活発", 1.0), ("元気", 0.9), ("明るい", 0.9),
        ("前向き", 0.9), ("エネルギッシュ", 1.0), ("活動的", 0.9),
        ("率先", 0.8), ("意欲", 0.8), ("やる気", 0.9), ("ポジティブ", 0.8),
    ],
    "focus": [
        ("真面目", 1.0), ("責任感", 1.0), ("几帳面", 0.9), ("集中", 0.9),
        ("誠実", 0.9), ("一生懸命", 0.9), ("粘り強", 0.9), ("丁寧に取り組", 0.8),
        ("確認", 0.6), ("慎重", 0.8), ("コツコツ", 0.8),
    ],
    "adaptability": [
        ("柔軟", 1.0), ("臨機応変", 1.0), ("対応力", 0.9), ("適応", 0.9),
        ("変化に強", 0.9), ("幅広く", 0.7), ("何でもこなす", 0.8),
        ("融通", 0.8), ("状況に応じ", 0.8), ("マルチ", 0.7),
    ],
    "communication": [
        ("コミュニケーション", 1.0), ("話しやすい", 0.9), ("会話", 0.7),
        ("表現力", 0.9), ("伝える", 0.7), ("聞き上手", 1.0), ("関係構築", 0.9),
        ("信頼関係", 0.9), ("チームワーク", 0.8), ("報告・連絡", 0.8),
    ],
}

_CARE_KEYWORD_MAPS: dict[str, list[str]] = {
    "mentioned_night_shift": [
        "夜勤", "夜間", "泊まり", "ナイト", "深夜", "夜間勤務",
    ],
    "mentioned_physical_care": [
        "身体介護", "入浴介助", "排泄介助", "移乗", "移動介助", "食事介助",
        "おむつ", "体位変換", "清拭", "口腔ケア",
    ],
    "mentioned_dementia": [
        "認知症", "物忘れ", "徘徊", "BPSD", "アルツハイマー",
        "レビー小体", "認知機能",
    ],
    "mentioned_disability": [
        "障害", "就労支援", "B型", "A型", "移行支援", "生活介護",
        "精神障害", "知的障害", "身体障害", "発達障害",
    ],
    "mentioned_group_living": [
        "共同生活", "グループホーム", "グループ生活", "一緒に生活",
        "少人数", "家庭的",
    ],
    "mentioned_activity": [
        "レクリエーション", "活動", "体操", "歌", "創作", "外出支援",
        "リハビリ", "運動", "ゲーム", "趣味",
    ],
}

_CONFIDENCE_KEYWORDS = [
    "得意", "経験があります", "自信", "できます", "やってきました",
    "実績", "担当してきた", "任されて", "専門", "資格",
]

_SATURATION = 3.0


def _score_trait(text: str, keywords: list[tuple[str, float]]) -> float:
    total = sum(weight for kw, weight in keywords if kw in text)
    return min(total / _SATURATION, 1.0)


def _extract_experience_years(text: str) -> int | None:
    m = re.search(r"(\d+)\s*年", text)
    return int(m.group(1)) if m else None


class KeywordAnalyzer(AnalyzerEngine):
    """キーワード辞書方式の解析エンジン。"""

    name = "keyword"

    def analyze(self, text: str) -> TextAnalysisResult:
        trait = TraitProfile(
            **{trait: _score_trait(text, kws)
               for trait, kws in _TRAIT_KEYWORDS.items()}
        )

        flag_values: dict[str, bool] = {
            field: any(kw in text for kw in kws)
            for field, kws in _CARE_KEYWORD_MAPS.items()
        }

        confidence_hits = sum(1 for kw in _CONFIDENCE_KEYWORDS if kw in text)
        confidence_score = min(confidence_hits / 3.0, 1.0)

        experience_years = _extract_experience_years(text)

        all_kws = [kw for kws in _CARE_KEYWORD_MAPS.values() for kw in kws]
        keywords = [kw for kw in all_kws if kw in text]

        features = TextFeatures(
            keywords=keywords,
            experience_years=experience_years,
            confidence_score=confidence_score,
            **flag_values,
        )

        hit_count = sum(1 for kws in _TRAIT_KEYWORDS.values()
                        for kw, _ in kws if kw in text)
        text_length_factor = min(len(text) / 200, 1.0)
        hit_factor = min(hit_count / 10, 1.0)
        analysis_confidence = round(
            (text_length_factor * 0.5 + hit_factor * 0.5), 2
        )

        return TextAnalysisResult(
            trait=trait,
            features=features,
            analysis_confidence=analysis_confidence,
        )
