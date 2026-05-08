"""
事業所適性スコアリングエンジン。
感情プロファイル・発話特性・希望条件を統合してスコアを算出する。
"""
import numpy as np
from app.models.candidate import CandidateProfile, ShiftPreference, WorkStyle
from app.models.facility import FacilityType
from app.data.facility_profiles import FACILITY_TRAIT_PROFILES

# 重み: 感情特性スコア 60% + キーワードボーナス 25% + 希望条件マッチ 15%
EMOTION_WEIGHT = 0.60
KEYWORD_WEIGHT = 0.25
CONDITION_WEIGHT = 0.15

_SHIFT_MAP = {
    ShiftPreference.DAY: "day",
    ShiftPreference.EVENING: "evening",
    ShiftPreference.NIGHT: "night",
    ShiftPreference.FLEXIBLE: "flexible",
}

_WORK_STYLE_MAP = {
    WorkStyle.FULL_TIME: "full_time",
    WorkStyle.PART_TIME: "part_time",
    WorkStyle.CONTRACT: "contract",
    WorkStyle.DISPATCH: "dispatch",
}


def _cosine_similarity(a: dict, b: dict) -> float:
    keys = list(a.keys())
    va = np.array([a[k] for k in keys], dtype=float)
    vb = np.array([b[k] for k in keys], dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def compute_score(profile: CandidateProfile, facility_type: FacilityType) -> tuple[float, list[str], list[str]]:
    """
    Returns (score_0_to_100, reasons, cautions)
    """
    fp = FACILITY_TRAIT_PROFILES[facility_type]
    emotion = profile.video_analysis.emotion
    speech = profile.video_analysis.speech
    candidate = profile.candidate

    # --- 1. 感情プロファイルのコサイン類似度 (0-1) ---
    candidate_emotion = {
        "calm": emotion.calm,
        "empathy": emotion.empathy,
        "energy": emotion.energy,
        "focus": emotion.focus,
        "adaptability": emotion.adaptability,
        "communication": emotion.communication,
    }
    emotion_score = _cosine_similarity(candidate_emotion, fp["emotion"])

    # --- 2. キーワードボーナス (0-1 に正規化) ---
    keyword_raw = 0.0
    max_bonus = 50.0  # 全ボーナス合計の理論最大値
    if speech.mentioned_night_shift:
        keyword_raw += fp["night_shift_bonus"]
    if speech.mentioned_dementia:
        keyword_raw += fp["dementia_bonus"]
    if speech.mentioned_physical_care:
        keyword_raw += fp["physical_care_bonus"]
    if speech.mentioned_disability:
        keyword_raw += fp["disability_bonus"]
    if speech.mentioned_activity:
        keyword_raw += fp["activity_bonus"]
    keyword_score = min(keyword_raw / max_bonus, 1.0)

    # --- 3. 希望条件マッチ (0-1) ---
    condition_score = 0.0
    shift_key = _SHIFT_MAP[candidate.shift_preference]
    if shift_key in fp["preferred_shifts"]:
        # preferred_shifts の先頭ほど高得点
        idx = fp["preferred_shifts"].index(shift_key)
        condition_score += 0.5 * (1.0 - idx / len(fp["preferred_shifts"]))
    work_key = _WORK_STYLE_MAP[candidate.work_style]
    if work_key in fp["preferred_work_styles"]:
        condition_score += 0.5

    # --- 総合スコア (0-100) ---
    raw = (
        emotion_score * EMOTION_WEIGHT
        + keyword_score * KEYWORD_WEIGHT
        + condition_score * CONDITION_WEIGHT
    )
    score = round(min(raw * 100, 100.0), 1)

    # --- 理由生成 ---
    reasons = _build_reasons(profile, facility_type, fp, emotion_score, keyword_raw)
    cautions = _build_cautions(profile, facility_type, fp)

    return score, reasons, cautions


def _build_reasons(
    profile: CandidateProfile,
    facility_type: FacilityType,
    fp: dict,
    emotion_score: float,
    keyword_raw: float,
) -> list[str]:
    reasons = []
    emotion = profile.video_analysis.emotion
    speech = profile.video_analysis.speech
    candidate = profile.candidate

    if emotion_score >= 0.85:
        reasons.append("面接の感情プロファイルがこの事業所の求める特性と高く一致しています")
    if emotion.calm >= 0.75 and fp["emotion"]["calm"] >= 0.8:
        reasons.append("穏やかで安定した対応力が認知症・高齢者ケアに適しています")
    if emotion.energy >= 0.75 and fp["emotion"]["energy"] >= 0.8:
        reasons.append("活発なエネルギーがレクリエーション支援に向いています")
    if emotion.adaptability >= 0.8 and fp["emotion"]["adaptability"] >= 0.9:
        reasons.append("高い柔軟性が多機能型サービスの変化に対応できます")
    if speech.mentioned_night_shift and fp["night_shift_bonus"] > 5:
        reasons.append("夜勤対応の意欲が明示されており夜間体制への適合度が高いです")
    if speech.mentioned_dementia and fp["dementia_bonus"] > 5:
        reasons.append("認知症ケアへの関心・経験が発話から確認できます")
    if speech.mentioned_disability and fp["disability_bonus"] > 10:
        reasons.append("障害福祉への理解と関心が発話から確認できます")
    if speech.mentioned_activity and fp["activity_bonus"] >= 10:
        reasons.append("レクリエーション・活動支援への関心が高く評価されます")
    shift_key = _SHIFT_MAP[candidate.shift_preference]
    if shift_key in fp["preferred_shifts"]:
        reasons.append(f"希望シフト（{candidate.shift_preference.value}）がこの事業所に適合しています")
    if candidate.has_care_manager_license:
        reasons.append("ケアマネジャー資格がケアプラン作成・連携業務に活かせます")

    return reasons if reasons else ["面接データと条件の総合評価でこの事業所への適合が認められます"]


def _build_cautions(
    profile: CandidateProfile,
    facility_type: FacilityType,
    fp: dict,
) -> list[str]:
    cautions = []
    emotion = profile.video_analysis.emotion
    speech = profile.video_analysis.speech
    candidate = profile.candidate

    if fp["night_shift_bonus"] > 10 and not speech.mentioned_night_shift:
        cautions.append("夜勤の意向が面接から確認できませんでした。事前の確認をお勧めします")
    if fp["disability_bonus"] > 10 and not speech.mentioned_disability:
        cautions.append("障害福祉への言及がなく、就労支援業務への理解確認が必要です")
    if emotion.adaptability < 0.5 and fp["emotion"]["adaptability"] >= 0.9:
        cautions.append("柔軟性スコアが低めです。多機能型業務の変化への対応をフォローアップ面談で確認してください")
    if profile.video_analysis.analysis_confidence < 0.5:
        cautions.append("動画解析の信頼度が低いため、補足面談での直接確認を推奨します")

    return cautions
