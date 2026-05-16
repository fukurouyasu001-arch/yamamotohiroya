"""
解析エンジンの抽象インターフェース。
キーワード方式・LLM方式など実装を差し替え可能にする。
"""
from abc import ABC, abstractmethod
from app.models.candidate import TextAnalysisResult


class AnalyzerEngine(ABC):
    """面接テキスト解析エンジンの共通インターフェース"""

    name: str = "base"

    @abstractmethod
    def analyze(self, text: str) -> TextAnalysisResult:
        """
        面接テキストを解析して特性スコアと介護分野フラグを返す。

        Args:
            text: 前処理済みの面接テキスト
        Returns:
            TextAnalysisResult: 特性 + フラグ + 信頼度
        """
        ...

    def healthcheck(self) -> bool:
        """エンジンが利用可能か返す。LLMでは接続確認に使う。"""
        return True
