from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class WorkStyle(str, Enum):
    FULL_TIME = "full_time"       # 正社員
    PART_TIME = "part_time"       # パート・アルバイト
    CONTRACT = "contract"         # 契約社員
    DISPATCH = "dispatch"         # 派遣


class ShiftPreference(str, Enum):
    DAY = "day"                   # 日勤のみ
    EVENING = "evening"           # 夕方・夜
    NIGHT = "night"               # 夜勤あり
    FLEXIBLE = "flexible"         # 柔軟


class EmotionProfile(BaseModel):
    """面接動画の感情解析結果"""
    calm: float = Field(ge=0.0, le=1.0, description="穏やかさ・安定性")
    empathy: float = Field(ge=0.0, le=1.0, description="共感力・温かさ")
    energy: float = Field(ge=0.0, le=1.0, description="活動性・明るさ")
    focus: float = Field(ge=0.0, le=1.0, description="集中力・真面目さ")
    adaptability: float = Field(ge=0.0, le=1.0, description="柔軟性・適応力")
    communication: float = Field(ge=0.0, le=1.0, description="コミュニケーション力")


class SpeechProfile(BaseModel):
    """発話内容の解析結果（Whisper + NLP）"""
    transcript: str = Field(description="発話テキスト全文")
    keywords: list[str] = Field(default_factory=list, description="抽出キーワード")
    experience_years: Optional[int] = Field(None, description="経験年数（発話から推定）")
    mentioned_night_shift: bool = Field(False, description="夜勤可と発言したか")
    mentioned_physical_care: bool = Field(False, description="身体介護に言及したか")
    mentioned_dementia: bool = Field(False, description="認知症ケアへの言及")
    mentioned_disability: bool = Field(False, description="障害福祉への言及")
    mentioned_group_living: bool = Field(False, description="共同生活・グループへの言及")
    mentioned_activity: bool = Field(False, description="レクリエーション・活動への言及")
    confidence_score: float = Field(ge=0.0, le=1.0, description="発話の自信度")


class CandidateInput(BaseModel):
    """応募者の希望条件（フォーム入力）"""
    name: str
    work_style: WorkStyle
    shift_preference: ShiftPreference
    preferred_hours_per_week: Optional[int] = Field(None, ge=1, le=60)
    has_care_worker_license: bool = False
    has_care_manager_license: bool = False
    has_social_worker_license: bool = False
    commute_limit_minutes: Optional[int] = Field(None, description="通勤許容時間（分）")
    notes: Optional[str] = None


class VideoAnalysisResult(BaseModel):
    """動画AI解析の統合結果"""
    emotion: EmotionProfile
    speech: SpeechProfile
    video_duration_seconds: float
    analysis_confidence: float = Field(ge=0.0, le=1.0)


class CandidateProfile(BaseModel):
    """応募者の総合プロファイル"""
    candidate: CandidateInput
    video_analysis: VideoAnalysisResult
