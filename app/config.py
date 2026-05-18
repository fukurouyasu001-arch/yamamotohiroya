"""
アプリケーション設定。
解析エンジンの切り替えなどはここを起点に環境変数で制御する。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── 解析エンジン選択 ──
    # "keyword": 現状のキーワード辞書方式（オフライン・軽量）
    # "llm":     オンプレLLM方式（要 Ollama / vLLM 接続）
    analyzer_engine: str = "keyword"

    # ── LLM 接続設定（"llm" モード時のみ使用） ──
    llm_endpoint: str = "http://localhost:11434"
    # CPU で動く軽量モデル（PoC 用）。GPU があれば qwen2.5:14b などに変更
    llm_model: str = "llama3.2:3b"
    llm_timeout_seconds: int = 120
    # LLM 失敗時にキーワード方式へ自動降格するか
    llm_fallback_to_keyword: bool = True

    # ── DB ──
    database_url: str = "sqlite:///./matching.db"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
