"""
事業所マッチングエンドポイント。
"""
from fastapi import APIRouter, HTTPException
from app.models.candidate import CandidateProfile
from app.models.facility import MatchingResponse
from app.services.matcher import run_matching

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/", response_model=MatchingResponse)
async def match_facility(profile: CandidateProfile):
    """
    応募者プロファイル（フォーム入力 + 動画解析結果）を受け取り、
    適合する事業所タイプをスコア順にランキングして返す。
    """
    try:
        return run_matching(profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"マッチング処理エラー: {str(e)}")


@router.post("/full-pipeline", response_model=MatchingResponse)
async def full_pipeline(profile: CandidateProfile):
    """
    /interview/analyze の結果を含む CandidateProfile を直接受け取り、
    ワンステップでマッチング結果を返す統合エンドポイント。
    """
    return run_matching(profile)
