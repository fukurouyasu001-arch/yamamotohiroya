"""
設定に基づき適切な解析エンジンを生成するファクトリ。
"""
from app.config import settings
from app.services.analyzer.base import AnalyzerEngine
from app.services.analyzer.keyword import KeywordAnalyzer
from app.services.analyzer.llm import LLMAnalyzer


def get_analyzer() -> AnalyzerEngine:
    """
    settings.analyzer_engine に応じた解析エンジンを返す。

    - "keyword": KeywordAnalyzer（デフォルト・オフライン）
    - "llm":     LLMAnalyzer（未実装、オンプレ LLM 接続後に使用）
    """
    engine = settings.analyzer_engine.lower()

    if engine == "llm":
        return LLMAnalyzer(
            endpoint=settings.llm_endpoint,
            model=settings.llm_model,
            timeout=settings.llm_timeout_seconds,
        )

    return KeywordAnalyzer()
