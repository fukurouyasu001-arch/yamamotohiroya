import json
from sqlalchemy.orm import Session
from app.db.models import MatchingRecord
from app.models.candidate import InterviewTextRequest, TextAnalysisResult
from app.models.facility import MatchingResponse


def save_result(
    db: Session,
    request: InterviewTextRequest,
    analysis: TextAnalysisResult,
    result: MatchingResponse,
) -> MatchingRecord:
    top = result.recommended_facilities[0]
    record = MatchingRecord(
        candidate_name=request.candidate.name,
        work_style=request.candidate.work_style.value,
        shift_preference=request.candidate.shift_preference.value,
        preferred_hours_per_week=request.candidate.preferred_hours_per_week,
        has_care_worker_license=request.candidate.has_care_worker_license,
        has_care_manager_license=request.candidate.has_care_manager_license,
        has_social_worker_license=request.candidate.has_social_worker_license,
        interview_text=request.interview_text,
        trait_profile_json=analysis.trait.model_dump_json(),
        text_features_json=analysis.features.model_dump_json(),
        analysis_confidence=analysis.analysis_confidence,
        facility_rankings_json=json.dumps(
            [f.model_dump() for f in result.recommended_facilities],
            ensure_ascii=False,
        ),
        top_facility_label=top.label,
        top_score=top.score,
        summary=result.summary,
        analysis_notes=result.analysis_notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_record(db: Session, record_id: int) -> MatchingRecord | None:
    return db.query(MatchingRecord).filter(MatchingRecord.id == record_id).first()


def list_records(db: Session, skip: int = 0, limit: int = 100) -> list[MatchingRecord]:
    return (
        db.query(MatchingRecord)
        .order_by(MatchingRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_record(db: Session, record_id: int) -> bool:
    record = get_record(db, record_id)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True
