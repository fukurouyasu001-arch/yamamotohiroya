"""
事業所適性スコアリングエンジン。
TraitProfile・TextFeatures・希望条件を統合してスコアを算出する。
"""
import numpy as np
from app.models.candidate import CandidateProfile, ShiftPreference, WorkStyle
from app.models.facility import FacilityType
from app.data.facility_profiles import FACILITY_TRAIT_PROFILES

TRAIT_WEIGHT = 0.60
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
    """Returns (score_0_to_100, reasons, cautions)"""
    fp = FACILITY_TRAIT_PROFILES[facility_type]
    trait = profile.analysis.trait
    features = profile.analysis.features
    candidate = profile.candidate

    # 1. 特性プロファイルのコサイン類似度 (0-1)
    candidate_trait = {
        "calm": trait.calm,
        "empathy": trait.empathy,
        "energy": trait.energy,
        "focus": trait.focus,
        "adaptability": trait.adaptability,
        "communication": trait.communication,
    }
    trait_score = _cosine_similarity(candidate_trait, fp["emotion"])

    # 2. キーワードボーナス (0-1 に正規化)
    max_bonus = 50.0
    keyword_raw = 0.0
    if features.mentioned_night_shift:
        keyword_raw += fp["night_shift_bonus"]
    if features.mentioned_dementia:
        keyword_raw += fp["dementia_bonus"]
    if features.mentioned_physical_care:
        keyword_raw += fp["physical_care_bonus"]
    if features.mentioned_disability:
        keyword_raw += fp["disability_bonus"]
    if features.mentioned_activity:
        keyword_raw += fp["activity_bonus"]
    keyword_score = min(keyword_raw / max_bonus, 1.0)

    # 3. 希望条件マッチ (0-1)
    condition_score = 0.0
    shift_key = _SHIFT_MAP[candidate.shift_preference]
    if shift_key in fp["preferred_shifts"]:
        idx = fp["preferred_shifts"].index(shift_key)
        condition_score += 0.5 * (1.0 - idx / len(fp["preferred_shifts"]))
    work_key = _WORK_STYLE_MAP[candidate.work_style]
    if work_key in fp["preferred_work_styles"]:
        condition_score += 0.5

    raw = (
        trait_score * TRAIT_WEIGHT
        + keyword_score * KEYWORD_WEIGHT
        + condition_score * CONDITION_WEIGHT
    )
    score = round(min(raw * 100, 100.0), 1)

    reasons = _build_reasons(profile, facility_type, fp, trait_score, keyword_raw)
    cautions = _build_cautions(profile, facility_type, fp)

    return score, reasons, cautions


def _build_reasons(
    profile: CandidateProfile,
    facility_type: FacilityType,
    fp: dict,
    trait_score: float,
    keyword_raw: float,
) -> list[str]:
    reasons = []
    trait = profile.analysis.trait
    features = profile.analysis.features
    candidate = profile.candidate

    if trait_score >= 0.85:
        reasons.append("面接テキストの特性プロファイルがこの事業所の求める人物像と高く一致しています")
    if trait.calm >= 0.7 and fp["emotion"]["calm"] >= 0.8:
        reasons.append("穏やかで安定した対応力が認知症・高齢者ケアに適しています")
    if trait.energy >= 0.7 and fp["emotion"]["energy"] >= 0.8:
        reasons.append("活発なエネルギーがレクリエーション支援・デイ業務に向いています")
    if trait.adaptability >= 0.7 and fp["emotion"]["adaptability"] >= 0.9:
        reasons.append("高い柔軟性が多機能型サービスの変化に対応できます")
    if trait.empathy >= 0.7 and fp["emotion"]["empathy"] >= 0.8:
        reasons.append("共感力・傾聴姿勢がご利用者との信頼関係構築に活かせます")
    if features.mentioned_night_shift and fp["night_shift_bonus"] > 5:
        reasons.append("夜勤対応の意欲が確認でき、夜間体制への適合度が高いです")
    if features.mentioned_dementia and fp["dementia_bonus"] > 5:
        reasons.append("認知症ケアへの関心・理解が面接テキストから確認できます")
    if features.mentioned_disability and fp["disability_bonus"] > 10:
        reasons.append("障害福祉への理解と関心が面接テキストから確認できます")
    if features.mentioned_activity and fp["activity_bonus"] >= 10:
        reasons.append("レクリエーション・活動支援への関心が高く評価されます")
    shift_key = candidate.shift_preference.value
    if any(shift_key in s for s in fp["preferred_shifts"]):
        reasons.append(f"希望シフトがこの事業所の勤務体制に適合しています")
    if candidate.has_care_manager_license:
        reasons.append("ケアマネジャー資格がケアプラン作成・連携業務に活かせます")

    return reasons if reasons else ["面接テキストと希望条件の総合評価でこの事業所への適合が認められます"]


def _build_cautions(
    profile: CandidateProfile,
    facility_type: FacilityType,
    fp: dict,
) -> list[str]:
    cautions = []
    trait = profile.analysis.trait
    features = profile.analysis.features

    if fp["night_shift_bonus"] > 10 and not features.mentioned_night_shift:
        cautions.append("夜勤への意向が面接テキストから確認できませんでした。事前確認をお勧めします")
    if fp["disability_bonus"] > 10 and not features.mentioned_disability:
        cautions.append("障害福祉への言及がなく、就労支援業務への理解確認が必要です")
    if trait.adaptability < 0.4 and fp["emotion"]["adaptability"] >= 0.9:
        cautions.append("柔軟性の特性が低めです。多機能型業務の変化への対応をフォローアップ面談で確認してください")
    if profile.analysis.analysis_confidence < 0.4:
        cautions.append("テキスト解析の信頼度が低いため、補足面談での直接確認を推奨します")

    return cautions
