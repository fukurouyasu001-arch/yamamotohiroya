"""
面接動画アップロード・解析エンドポイント。
"""
import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
import aiofiles

from app.services.video_analyzer import analyze_video
from app.models.candidate import VideoAnalysisResult

router = APIRouter(prefix="/interview", tags=["interview"])

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
MAX_FILE_SIZE_MB = 500


@router.post("/analyze", response_model=VideoAnalysisResult)
async def analyze_interview_video(video: UploadFile = File(...)):
    """
    面接動画をアップロードして AI 解析結果を返す。
    - 表情・感情解析（DeepFace）
    - 発話テキスト化・特性抽出（Whisper）
    """
    ext = os.path.splitext(video.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"対応形式: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = tmp.name

    try:
        async with aiofiles.open(tmp_path, "wb") as f:
            content = await video.read()
            if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=413, detail=f"ファイルサイズは{MAX_FILE_SIZE_MB}MB以下にしてください")
            await f.write(content)

        result = await analyze_video(tmp_path)
        return result
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
