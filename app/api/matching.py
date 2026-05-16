"""
事業所マッチングエンドポイント。
解析エンジンはファクトリ経由で差し替え可能（キーワード辞書 / オンプレLLM）。
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.crud import save_result
from app.models.candidate import InterviewTextRequest, CandidateProfile
from app.models.facility import MatchingResponse
from app.services.notebooklm_preprocessor import preprocess
from app.services.analyzer import get_analyzer
from app.services.matcher import run_matching

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/", response_model=MatchingResponse)
async def match_facility(
    request: InterviewTextRequest,
    db: Session = Depends(get_db),
):
    """
    面接テキストと希望条件を受け取り、適合する介護事業所をランキングしてDB保存する。

    解析エンジンは settings.analyzer_engine で切り替え可能:
      - "keyword": オフラインのキーワード辞書方式（デフォルト）
      - "llm":     オンプレLLM接続方式（実装予定）
    """
    try:
        cleaned_text = preprocess(request.interview_text)

        analyzer = get_analyzer()
        analysis = analyzer.analyze(cleaned_text)

        profile = CandidateProfile(candidate=request.candidate, analysis=analysis)
        result = run_matching(profile)

        cleaned_request = request.model_copy(update={"interview_text": cleaned_text})
        record = save_result(db, cleaned_request, analysis, result)

        return result.model_copy(update={"record_id": record.id})
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"マッチング処理エラー: {str(e)}")
