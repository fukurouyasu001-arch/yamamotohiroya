"""
各事業所タイプに求められる特性プロファイル定義。
スコアリングエンジンはこれを基準としてコサイン類似度を計算する。
"""
from app.models.facility import FacilityType

# 各事業所の「理想的な職員特性ベクトル」
# キー: EmotionProfile の各フィールドに対応
FACILITY_TRAIT_PROFILES: dict[FacilityType, dict] = {
    FacilityType.GROUP_HOME: {
        "emotion": {
            "calm": 0.9,
            "empathy": 0.9,
            "energy": 0.5,
            "focus": 0.7,
            "adaptability": 0.6,
            "communication": 0.7,
        },
        "night_shift_bonus": 15.0,       # 夜勤可への加点
        "dementia_bonus": 12.0,           # 認知症ケア言及への加点
        "physical_care_bonus": 8.0,
        "disability_bonus": 0.0,
        "activity_bonus": 3.0,
        "preferred_shifts": ["night", "flexible", "day"],
        "preferred_work_styles": ["full_time", "part_time", "contract"],
        "description": "少人数の認知症高齢者と密な関係を築く夜間も含む生活支援",
    },
    FacilityType.DAY_SERVICE: {
        "emotion": {
            "calm": 0.6,
            "empathy": 0.8,
            "energy": 0.9,
            "focus": 0.6,
            "adaptability": 0.7,
            "communication": 0.9,
        },
        "night_shift_bonus": 0.0,
        "dementia_bonus": 5.0,
        "physical_care_bonus": 6.0,
        "disability_bonus": 0.0,
        "activity_bonus": 15.0,
        "preferred_shifts": ["day", "flexible"],
        "preferred_work_styles": ["full_time", "part_time", "contract", "dispatch"],
        "description": "日帰りの集団レクリエーション・生活リハビリを元気に支援",
    },
    FacilityType.SMALL_SCALE_MULTI: {
        "emotion": {
            "calm": 0.7,
            "empathy": 0.8,
            "energy": 0.7,
            "focus": 0.7,
            "adaptability": 0.95,
            "communication": 0.8,
        },
        "night_shift_bonus": 10.0,
        "dementia_bonus": 8.0,
        "physical_care_bonus": 7.0,
        "disability_bonus": 0.0,
        "activity_bonus": 5.0,
        "preferred_shifts": ["flexible", "day", "night"],
        "preferred_work_styles": ["full_time", "contract"],
        "description": "通所・訪問・泊まりを柔軟に組み合わせるオールラウンドケア",
    },
    FacilityType.EMPLOYMENT_SUPPORT: {
        "emotion": {
            "calm": 0.8,
            "empathy": 0.85,
            "energy": 0.6,
            "focus": 0.9,
            "adaptability": 0.7,
            "communication": 0.8,
        },
        "night_shift_bonus": 0.0,
        "dementia_bonus": 0.0,
        "physical_care_bonus": 2.0,
        "disability_bonus": 20.0,
        "activity_bonus": 8.0,
        "preferred_shifts": ["day", "flexible"],
        "preferred_work_styles": ["full_time", "contract", "part_time"],
        "description": "障害のある方の就労・生活を計画的にサポート",
    },
    FacilityType.HOME_CARE: {
        "emotion": {
            "calm": 0.7,
            "empathy": 0.9,
            "energy": 0.7,
            "focus": 0.8,
            "adaptability": 0.8,
            "communication": 0.85,
        },
        "night_shift_bonus": 5.0,
        "dementia_bonus": 7.0,
        "physical_care_bonus": 15.0,
        "disability_bonus": 5.0,
        "activity_bonus": 2.0,
        "preferred_shifts": ["day", "flexible", "evening"],
        "preferred_work_styles": ["full_time", "part_time", "dispatch"],
        "description": "ご利用者宅を単独訪問し身体介護・生活援助を担う",
    },
    FacilityType.SPECIAL_NURSING: {
        "emotion": {
            "calm": 0.8,
            "empathy": 0.8,
            "energy": 0.65,
            "focus": 0.85,
            "adaptability": 0.6,
            "communication": 0.75,
        },
        "night_shift_bonus": 12.0,
        "dementia_bonus": 10.0,
        "physical_care_bonus": 12.0,
        "disability_bonus": 0.0,
        "activity_bonus": 4.0,
        "preferred_shifts": ["night", "flexible", "day"],
        "preferred_work_styles": ["full_time", "contract"],
        "description": "重度要介護者への24時間体制の介護・看護連携",
    },
}
