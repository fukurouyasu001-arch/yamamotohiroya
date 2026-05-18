"""
システム・エンジン状態の確認エンドポイント。
Ollama の疎通確認・使用中モデルの確認に使う。
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings
from app.services.analyzer import get_analyzer
from app.services.analyzer.llm import LLMAnalyzer

router = APIRouter(prefix="/health", tags=["health"])


class EngineStatus(BaseModel):
    engine: str
    model: str | None
    ollama_reachable: bool | None
    installed_models: list[str]
    fallback_enabled: bool | None
    status: str


@router.get("/engine", response_model=EngineStatus)
def engine_status():
    """
    現在の解析エンジンと Ollama の状態を返す。
    Ollama 接続の確認・モデルのインストール確認に使用する。
    """
    analyzer = get_analyzer()

    if isinstance(analyzer, LLMAnalyzer):
        reachable = analyzer.healthcheck()
        installed = analyzer.list_models() if reachable else []
        model_ok = any(settings.llm_model in m for m in installed)
        status = (
            "ok" if reachable and model_ok
            else "model_not_found" if reachable
            else "ollama_unreachable"
        )
        return EngineStatus(
            engine="llm",
            model=settings.llm_model,
            ollama_reachable=reachable,
            installed_models=installed,
            fallback_enabled=settings.llm_fallback_to_keyword,
            status=status,
        )

    return EngineStatus(
        engine="keyword",
        model=None,
        ollama_reachable=None,
        installed_models=[],
        fallback_enabled=None,
        status="ok",
    )
