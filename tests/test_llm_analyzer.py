"""
LLMAnalyzer の単体テスト。
requests をモックし、Ollama なしで動作検証する。
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.analyzer.llm import LLMAnalyzer


# ── テスト用 Ollama レスポンス ──────────────────────────────

def _ollama_response(trait: dict, features: dict, confidence: float = 0.85) -> dict:
    """/api/generate の正常レスポンスを生成するヘルパー。"""
    body = {
        "trait": trait,
        "features": {
            "mentioned_night_shift": features.get("night_shift", False),
            "mentioned_physical_care": features.get("physical_care", False),
            "mentioned_dementia": features.get("dementia", False),
            "mentioned_disability": features.get("disability", False),
            "mentioned_group_living": features.get("group_living", False),
            "mentioned_activity": features.get("activity", False),
            "experience_years": features.get("years"),
            "confidence_score": features.get("confidence", 0.6),
            "keywords": features.get("keywords", []),
        },
        "analysis_confidence": confidence,
    }
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {"response": json.dumps(body), "done": True}
    return mock


def _make_analyzer(fallback: bool = False) -> LLMAnalyzer:
    return LLMAnalyzer(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
        timeout=60,
        fallback=fallback,
    )


# ── 正常系 ──────────────────────────────────────────────────

def test_analyze_returns_trait_scores():
    mock = _ollama_response(
        trait={"calm": 0.9, "empathy": 0.85, "energy": 0.5,
               "focus": 0.7, "adaptability": 0.6, "communication": 0.75},
        features={"night_shift": True, "dementia": True, "years": 5,
                  "keywords": ["夜勤", "認知症"]},
        confidence=0.88,
    )
    with patch("requests.post", return_value=mock):
        result = _make_analyzer().analyze("夜勤も対応できます。認知症ケアに関心があります。5年経験。")

    assert result.trait.calm == 0.9
    assert result.trait.empathy == 0.85
    assert result.analysis_confidence == 0.88


def test_analyze_features_flags():
    mock = _ollama_response(
        trait={"calm": 0.7, "empathy": 0.8, "energy": 0.6,
               "focus": 0.8, "adaptability": 0.7, "communication": 0.8},
        features={"night_shift": True, "dementia": True, "years": 3,
                  "confidence": 0.7, "keywords": ["夜勤", "認知症"]},
    )
    with patch("requests.post", return_value=mock):
        result = _make_analyzer().analyze("テストテキスト")

    assert result.features.mentioned_night_shift is True
    assert result.features.mentioned_dementia is True
    assert result.features.experience_years == 3
    assert "夜勤" in result.features.keywords


def test_analyze_disability_flag():
    mock = _ollama_response(
        trait={"calm": 0.8, "empathy": 0.85, "energy": 0.6,
               "focus": 0.9, "adaptability": 0.7, "communication": 0.8},
        features={"disability": True, "confidence": 0.8},
    )
    with patch("requests.post", return_value=mock):
        result = _make_analyzer().analyze("就労支援で障害のある方を支援してきました。")

    assert result.features.mentioned_disability is True


def test_scores_clamped_to_valid_range():
    """LLM が 0-1 範囲外の値を返してもクランプされること。"""
    mock = _ollama_response(
        trait={"calm": 1.5, "empathy": -0.2, "energy": 0.5,
               "focus": 0.7, "adaptability": 0.6, "communication": 0.8},
        features={},
    )
    with patch("requests.post", return_value=mock):
        result = _make_analyzer().analyze("テスト")

    assert result.trait.calm == 1.0
    assert result.trait.empathy == 0.0


def test_experience_years_none_when_absent():
    mock = _ollama_response(
        trait={"calm": 0.6, "empathy": 0.7, "energy": 0.6,
               "focus": 0.6, "adaptability": 0.6, "communication": 0.7},
        features={"years": None},
    )
    with patch("requests.post", return_value=mock):
        result = _make_analyzer().analyze("介護に関心があります。")

    assert result.features.experience_years is None


# ── エラー・フォールバック系 ──────────────────────────────────

def test_fallback_to_keyword_when_ollama_unreachable():
    """Ollama に繋がらない場合、キーワード方式に降格すること。"""
    import requests as req_module
    with patch("requests.post", side_effect=req_module.ConnectionError("接続不可")):
        analyzer = _make_analyzer(fallback=True)
        # キーワード方式で解析できる内容なら何らかの結果が返ること
        result = analyzer.analyze("穏やかで認知症ケアに関心があります。夜勤も対応可能です。")

    assert result is not None
    # キーワード方式のフォールバックなので confidence は低め
    assert result.analysis_confidence >= 0.0


def test_no_fallback_raises_on_connection_error():
    """fallback=False の場合は例外が上がること。"""
    import requests as req_module
    with patch("requests.post", side_effect=req_module.ConnectionError("接続不可")):
        analyzer = _make_analyzer(fallback=False)
        with pytest.raises(Exception):
            analyzer.analyze("テスト")


def test_fallback_on_invalid_json_response():
    """LLM が不正な JSON を返した場合もフォールバックすること。"""
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {"response": "これはJSONではありません", "done": True}

    with patch("requests.post", return_value=mock):
        analyzer = _make_analyzer(fallback=True)
        result = analyzer.analyze("穏やかで認知症ケアに関心があります。")

    assert result is not None


# ── healthcheck ───────────────────────────────────────────────

def test_healthcheck_true_when_ollama_running():
    mock = MagicMock()
    mock.status_code = 200
    with patch("requests.get", return_value=mock):
        assert _make_analyzer().healthcheck() is True


def test_healthcheck_false_when_ollama_down():
    import requests as req_module
    with patch("requests.get", side_effect=req_module.ConnectionError):
        assert _make_analyzer().healthcheck() is False


def test_list_models_returns_names():
    mock = MagicMock()
    mock.status_code = 200
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        "models": [
            {"name": "llama3.2:3b"},
            {"name": "qwen2.5:7b"},
        ]
    }
    with patch("requests.get", return_value=mock):
        models = _make_analyzer().list_models()

    assert "llama3.2:3b" in models
    assert "qwen2.5:7b" in models
