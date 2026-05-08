from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from app.db.database import Base


class MatchingRecord(Base):
    """判定結果の永続化レコード。1判定 = 1行。"""
    __tablename__ = "matching_records"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── 応募者基本情報 ──
    candidate_name = Column(String(100), nullable=False, index=True)
    work_style = Column(String(20), nullable=False)
    shift_preference = Column(String(20), nullable=False)
    preferred_hours_per_week = Column(Integer, nullable=True)
    has_care_worker_license = Column(Boolean, default=False)
    has_care_manager_license = Column(Boolean, default=False)
    has_social_worker_license = Column(Boolean, default=False)

    # ── 元テキスト（NotebookLM出力） ──
    interview_text = Column(Text, nullable=False)

    # ── 解析・判定結果（JSON文字列） ──
    trait_profile_json = Column(Text, nullable=False)   # TraitProfile
    text_features_json = Column(Text, nullable=False)   # TextFeatures
    analysis_confidence = Column(Float, nullable=False)
    facility_rankings_json = Column(Text, nullable=False)  # list[FacilityMatchResult]

    # ── サマリー（検索・一覧表示用） ──
    top_facility_label = Column(String(50), nullable=False)
    top_score = Column(Float, nullable=False)
    summary = Column(Text, nullable=False)
    analysis_notes = Column(Text, nullable=False)
