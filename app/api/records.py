"""
判定履歴の参照・削除エンドポイント。
"""
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.db.crud import get_record, list_records, delete_record

router = APIRouter(prefix="/records", tags=["records"])


class RecordSummary(BaseModel):
    """一覧表示用の軽量レコード"""
    id: int
    created_at: datetime
    candidate_name: str
    work_style: str
    shift_preference: str
    top_facility_label: str
    top_score: float
    analysis_confidence: float
    summary: str


class RecordDetail(RecordSummary):
    """詳細表示用（全データ含む）"""
    interview_text: str
    trait_profile: dict
    text_features: dict
    facility_rankings: list[dict]
    analysis_notes: str
    has_care_worker_license: bool
    has_care_manager_license: bool
    has_social_worker_license: bool
    preferred_hours_per_week: Optional[int]


class RecordListResponse(BaseModel):
    total: int
    records: list[RecordSummary]


@router.get("/", response_model=RecordListResponse)
def list_all_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """判定履歴の一覧を新しい順で返す。"""
    records = list_records(db, skip=skip, limit=limit)
    return RecordListResponse(
        total=len(records),
        records=[
            RecordSummary(
                id=r.id,
                created_at=r.created_at,
                candidate_name=r.candidate_name,
                work_style=r.work_style,
                shift_preference=r.shift_preference,
                top_facility_label=r.top_facility_label,
                top_score=r.top_score,
                analysis_confidence=r.analysis_confidence,
                summary=r.summary,
            )
            for r in records
        ],
    )


@router.get("/{record_id}", response_model=RecordDetail)
def get_record_detail(record_id: int, db: Session = Depends(get_db)):
    """指定IDの判定結果の詳細を返す。"""
    record = get_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    return RecordDetail(
        id=record.id,
        created_at=record.created_at,
        candidate_name=record.candidate_name,
        work_style=record.work_style,
        shift_preference=record.shift_preference,
        preferred_hours_per_week=record.preferred_hours_per_week,
        has_care_worker_license=record.has_care_worker_license,
        has_care_manager_license=record.has_care_manager_license,
        has_social_worker_license=record.has_social_worker_license,
        top_facility_label=record.top_facility_label,
        top_score=record.top_score,
        analysis_confidence=record.analysis_confidence,
        summary=record.summary,
        analysis_notes=record.analysis_notes,
        interview_text=record.interview_text,
        trait_profile=json.loads(record.trait_profile_json),
        text_features=json.loads(record.text_features_json),
        facility_rankings=json.loads(record.facility_rankings_json),
    )


@router.delete("/{record_id}", status_code=204)
def delete_record_endpoint(record_id: int, db: Session = Depends(get_db)):
    """指定IDの判定レコードを削除する。"""
    if not delete_record(db, record_id):
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
