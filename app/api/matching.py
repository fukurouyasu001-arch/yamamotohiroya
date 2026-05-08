"""
事業所マッチングエンドポイント。
面接AIテキスト + 希望条件を受け取り、適合事業所をランキングしてDB保存する。
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.crud import save_result
from app.models.candidate import InterviewTextRequest, CandidateProfile
from app.models.facility import MatchingResponse
from app.services.notebooklm_preprocessor import preprocess
from app.services.text_analyzer import analyze_text
from app.services.matcher import run_matching

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/", response_model=MatchingResponse)
async def match_facility(
    request: InterviewTextRequest,
    db: Session = Depends(get_db),
):
    """
    NotebookLMで整形した面接テキストと希望条件を受け取り、
    適合する介護事業所をスコア順にランキングしてDBに保存する。

    - interview_text: Zoom録画 → NotebookLM で出力したテキスト
    - candidate: 希望の時間帯・働き方などの条件
    """
    try:
        cleaned_text = preprocess(request.interview_text)
        analysis = analyze_text(cleaned_text)
        profile = CandidateProfile(candidate=request.candidate, analysis=analysis)
        result = run_matching(profile)

        # DB保存（前処理済みテキストで保存）
        cleaned_request = request.model_copy(update={"interview_text": cleaned_text})
        record = save_result(db, cleaned_request, analysis, result)

        # レスポンスに保存IDを付加して返す
        return result.model_copy(update={"record_id": record.id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"マッチング処理エラー: {str(e)}")
