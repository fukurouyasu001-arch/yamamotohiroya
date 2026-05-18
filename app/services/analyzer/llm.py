"""
オンプレ LLM（Ollama）を使った解析エンジン。

接続先: Ollama  http://localhost:11434
推奨モデル（CPU 動作可）:
  - llama3.2:3b   … 最軽量・高速（PoC に最適）
  - qwen2.5:7b    … 日本語精度高め
  - gemma2:9b     … バランス型
GPU があれば:
  - qwen2.5:14b / llama3.3:70b

Ollama 未起動・モデル未インストール時は KeywordAnalyzer に自動降格する。
"""
import json
import logging
import re
from typing import Any

import requests
from pydantic import ValidationError

from app.models.candidate import TraitProfile, TextFeatures, TextAnalysisResult
from app.services.analyzer.base import AnalyzerEngine

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# プロンプト
# 小型モデルでも安定して JSON を出力できるよう、
# 指示を短く・具体的に保つ。Few-shot 例を 1 件埋め込んで精度を上げる。
# ─────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
あなたは介護採用の面接分析AIです。
面接テキストを読み、応募者の特性をJSONで出力してください。
JSONのみ出力し、説明文は不要です。

【出力形式】
{
  "trait": {
    "calm": 穏やかさ(0.0-1.0),
    "empathy": 共感力(0.0-1.0),
    "energy": 活動性(0.0-1.0),
    "focus": 集中力・責任感(0.0-1.0),
    "adaptability": 柔軟性(0.0-1.0),
    "communication": コミュニケーション力(0.0-1.0)
  },
  "features": {
    "mentioned_night_shift": 夜勤への前向きな意向(true/false),
    "mentioned_physical_care": 身体介護への言及(true/false),
    "mentioned_dementia": 認知症ケアへの関心(true/false),
    "mentioned_disability": 障害福祉への言及(true/false),
    "mentioned_group_living": 少人数・共同生活への適性(true/false),
    "mentioned_activity": レクリエーション・活動支援への関心(true/false),
    "experience_years": 介護経験年数(整数 or null),
    "confidence_score": 発言の自信度(0.0-1.0),
    "keywords": ["抽出キーワード"]
  },
  "analysis_confidence": 解析信頼度(0.0-1.0)
}

【重要ルール】
- 否定文（「夜勤はできない」）は false にすること
- テキストにない情報は 0.0 / false / null にすること
- JSONのみ出力すること（説明不要）

【出力例】
入力: 「認知症の祖母を介護した経験があり、夜勤も積極的に入りたいです。傾聴を大切にしています。」
出力:
{"trait":{"calm":0.7,"empathy":0.9,"energy":0.5,"focus":0.6,"adaptability":0.5,"communication":0.8},"features":{"mentioned_night_shift":true,"mentioned_physical_care":false,"mentioned_dementia":true,"mentioned_disability":false,"mentioned_group_living":false,"mentioned_activity":false,"experience_years":null,"confidence_score":0.6,"keywords":["認知症","夜勤","傾聴"]},"analysis_confidence":0.8}

【面接テキスト】
"""

# JSON 抽出用（LLM が余分なテキストを含む場合の保険）
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

# LLM 出力に対応する TextAnalysisResult のデフォルト値
_DEFAULT_RESULT = TextAnalysisResult(
    trait=TraitProfile(calm=0.5, empathy=0.5, energy=0.5,
                       focus=0.5, adaptability=0.5, communication=0.5),
    features=TextFeatures(confidence_score=0.0),
    analysis_confidence=0.0,
)


class LLMAnalyzer(AnalyzerEngine):
    """Ollama 経由のオンプレ LLM 解析エンジン。"""

    name = "llm"

    def __init__(self, endpoint: str, model: str, timeout: int, fallback: bool = True):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.fallback = fallback

    # ── 公開 API ─────────────────────────────────────────────

    def analyze(self, text: str) -> TextAnalysisResult:
        try:
            raw_json = self._call_ollama(text)
            return self._parse(raw_json)
        except Exception as exc:
            logger.warning("LLMAnalyzer 失敗 (%s): %s", type(exc).__name__, exc)
            if self.fallback:
                logger.info("KeywordAnalyzer にフォールバックします")
                from app.services.analyzer.keyword import KeywordAnalyzer
                return KeywordAnalyzer().analyze(text)
            raise

    def healthcheck(self) -> bool:
        """Ollama が起動しているか確認する。"""
        try:
            r = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """インストール済みモデルの一覧を返す。"""
        try:
            r = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    # ── 内部実装 ─────────────────────────────────────────────

    def _call_ollama(self, text: str) -> dict[str, Any]:
        """Ollama /api/generate を呼び出し、JSON dict を返す。"""
        prompt = _SYSTEM_PROMPT + text.strip()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",   # Ollama の JSON モード（構造化出力を強制）
            "stream": False,
            "options": {
                "temperature": 0.1,   # 低温で安定した出力
                "num_predict": 512,   # 出力トークン上限
            },
        }
        response = requests.post(
            f"{self.endpoint}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()

        raw_text = result.get("response", "")
        if not raw_text:
            raise ValueError("Ollama からの応答が空でした")

        # JSON 部分のみ抽出（余分な前後テキストへの保険）
        m = _JSON_RE.search(raw_text)
        if not m:
            raise ValueError(f"JSON が見つかりません: {raw_text[:200]}")

        return json.loads(m.group())

    def _parse(self, data: dict[str, Any]) -> TextAnalysisResult:
        """LLM の出力 dict を TextAnalysisResult に変換・検証する。"""
        try:
            trait_raw = data.get("trait", {})
            features_raw = data.get("features", {})

            trait = TraitProfile(
                calm=self._clamp(trait_raw.get("calm", 0.5)),
                empathy=self._clamp(trait_raw.get("empathy", 0.5)),
                energy=self._clamp(trait_raw.get("energy", 0.5)),
                focus=self._clamp(trait_raw.get("focus", 0.5)),
                adaptability=self._clamp(trait_raw.get("adaptability", 0.5)),
                communication=self._clamp(trait_raw.get("communication", 0.5)),
            )

            features = TextFeatures(
                mentioned_night_shift=bool(features_raw.get("mentioned_night_shift", False)),
                mentioned_physical_care=bool(features_raw.get("mentioned_physical_care", False)),
                mentioned_dementia=bool(features_raw.get("mentioned_dementia", False)),
                mentioned_disability=bool(features_raw.get("mentioned_disability", False)),
                mentioned_group_living=bool(features_raw.get("mentioned_group_living", False)),
                mentioned_activity=bool(features_raw.get("mentioned_activity", False)),
                experience_years=self._to_int(features_raw.get("experience_years")),
                confidence_score=self._clamp(features_raw.get("confidence_score", 0.5)),
                keywords=list(features_raw.get("keywords", [])),
            )

            confidence = self._clamp(data.get("analysis_confidence", 0.7))

            return TextAnalysisResult(
                trait=trait,
                features=features,
                analysis_confidence=confidence,
            )

        except (ValidationError, TypeError, KeyError) as exc:
            raise ValueError(f"LLM 出力のパース失敗: {exc}") from exc

    @staticmethod
    def _clamp(val: Any) -> float:
        try:
            return max(0.0, min(1.0, float(val)))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _to_int(val: Any) -> int | None:
        try:
            return int(val)
        except (TypeError, ValueError):
            return None
