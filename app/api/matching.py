"""
事業所マッチングエンドポイント。
面接AIテキスト + 希望条件を受け取り、適合事業所をランキングして返す。
"""
from fastapi import APIRouter, HTTPException
from app.models.candidate import InterviewTextRequest, CandidateProfile
from app.models.facility import MatchingResponse
from app.services.text_analyzer import analyze_text
from app.services.matcher import run_matching

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/", response_model=MatchingResponse)
async def match_facility(request: InterviewTextRequest):
    """
    面接動画をAIで解析したテキストデータと希望条件を受け取り、
    適合する介護事業所タイプをスコア順にランキングして返す。

    - interview_text: 面接AI解析済みテキスト（自由記述）
    - candidate: 希望の時間帯・働き方などの条件
    """
    try:
        analysis = analyze_text(request.interview_text)
        profile = CandidateProfile(candidate=request.candidate, analysis=analysis)
        return run_matching(profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"マッチング処理エラー: {str(e)}")
