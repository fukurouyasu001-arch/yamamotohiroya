from pydantic import BaseModel, Field
from enum import Enum


class FacilityType(str, Enum):
    GROUP_HOME = "group_home"                 # グループホーム
    DAY_SERVICE = "day_service"               # デイサービス
    SMALL_SCALE_MULTI = "small_scale_multi"   # 小規模多機能型居宅介護
    EMPLOYMENT_SUPPORT = "employment_support" # 就労支援（障害福祉）
    HOME_CARE = "home_care"                   # 訪問介護
    SPECIAL_NURSING = "special_nursing"       # 特別養護老人ホーム


FACILITY_LABELS = {
    FacilityType.GROUP_HOME: "グループホーム",
    FacilityType.DAY_SERVICE: "デイサービス",
    FacilityType.SMALL_SCALE_MULTI: "小規模多機能型居宅介護",
    FacilityType.EMPLOYMENT_SUPPORT: "就労支援（障害福祉）",
    FacilityType.HOME_CARE: "訪問介護",
    FacilityType.SPECIAL_NURSING: "特別養護老人ホーム",
}


class FacilityMatchResult(BaseModel):
    facility_type: FacilityType
    label: str
    score: float = Field(ge=0.0, le=100.0, description="適合スコア（0-100）")
    rank: int
    reasons: list[str] = Field(description="この事業所が推奨される理由")
    cautions: list[str] = Field(default_factory=list, description="注意点・懸念事項")


class MatchingResponse(BaseModel):
    candidate_name: str
    recommended_facilities: list[FacilityMatchResult]
    summary: str
    analysis_notes: str
