"""
LLM 統合テスト（モック Ollama サーバー使用）。

実際の Ollama + llama3.2:3b と同じ HTTP 通信フローを再現し、
LLMAnalyzer の実装を end-to-end で検証する。
"""
import pytest

from tests.mock_ollama import MockOllamaServer
from app.services.analyzer.llm import LLMAnalyzer
from app.models.facility import FacilityType
from app.models.candidate import CandidateConditions, CandidateProfile, WorkStyle, ShiftPreference
from app.services.scorer import compute_score
from app.services.matcher import run_matching


@pytest.fixture(scope="module")
def ollama_server():
    """モジュール全体で共有するモックサーバー。"""
    server = MockOllamaServer(port=11435)
    server.start()
    yield server
    server.stop()


@pytest.fixture
def llm(ollama_server):
    return LLMAnalyzer(
        endpoint=ollama_server.endpoint,
        model="llama3.2:3b",
        timeout=10,
        fallback=False,
    )


# ── 接続・ヘルスチェック ─────────────────────────────────────

def test_healthcheck_passes(llm):
    assert llm.healthcheck() is True


def test_list_models_includes_target(llm):
    models = llm.list_models()
    assert "llama3.2:3b" in models


# ── 解析結果の検証 ───────────────────────────────────────────

def test_group_home_candidate_analyzed(llm):
    """グループホーム向き応募者テキストを正しく解析できること。"""
    text = "穏やかで落ち着いた性格です。認知症の祖母を介護した経験があります。夜勤も対応できます。傾聴を大切にしています。"
    result = llm.analyze(text)

    assert result.trait.calm > 0.0
    assert result.trait.empathy > 0.0
    assert result.features.mentioned_dementia is True
    assert result.features.mentioned_night_shift is True
    assert result.analysis_confidence >= 0.0


def test_day_service_candidate_analyzed(llm):
    """デイサービス向き応募者テキストを正しく解析できること。"""
    text = "明るく積極的に活動支援をしてきました。レクリエーションや体操が得意です。元気よく利用者と関わります。"
    result = llm.analyze(text)

    assert result.trait.energy > 0.0
    assert result.features.mentioned_activity is True


def test_disability_candidate_analyzed(llm):
    """就労支援向き応募者テキストを正しく解析できること。"""
    text = "就労支援B型で障害のある方の支援をしてきました。精神障害・知的障害への理解があります。"
    result = llm.analyze(text)

    assert result.features.mentioned_disability is True


def test_experience_years_extracted(llm):
    result = llm.analyze("介護の仕事を5年続けてきました。")
    assert result.features.experience_years == 5


# ── マッチングエンジンとの結合テスト ─────────────────────────

def _make_profile_via_llm(llm, text: str, shift=ShiftPreference.NIGHT) -> CandidateProfile:
    candidate = CandidateConditions(
        name="テスト",
        work_style=WorkStyle.FULL_TIME,
        shift_preference=shift,
    )
    analysis = llm.analyze(text)
    return CandidateProfile(candidate=candidate, analysis=analysis)


def test_llm_to_matching_group_home(llm):
    """LLM 解析 → マッチング が正常に動作すること。"""
    text = "穏やかで夜勤も対応できます。認知症の祖母を介護した経験があります。"
    profile = _make_profile_via_llm(llm, text, shift=ShiftPreference.NIGHT)

    score, reasons, _ = compute_score(profile, FacilityType.GROUP_HOME)
    assert score > 0
    assert len(reasons) > 0


def test_llm_to_full_matching_pipeline(llm):
    """LLM 解析 → 全事業所ランキング が正常に動作すること。"""
    text = (
        "穏やかで落ち着いた性格。夜勤も積極的に入りたい。"
        "認知症ケアに強い関心があります。傾聴と共感を大切にしています。"
    )
    profile = _make_profile_via_llm(llm, text)
    result = run_matching(profile)

    assert len(result.recommended_facilities) == len(FacilityType)
    scores = [f.score for f in result.recommended_facilities]
    assert scores == sorted(scores, reverse=True)


def test_matching_summary_contains_name(llm):
    text = "真面目に責任感を持って取り組みます。"
    candidate = CandidateConditions(
        name="山田花子",
        work_style=WorkStyle.PART_TIME,
        shift_preference=ShiftPreference.DAY,
    )
    analysis = llm.analyze(text)
    profile = CandidateProfile(candidate=candidate, analysis=analysis)
    result = run_matching(profile)

    assert "山田花子" in result.summary


# ── フォールバック動作 ───────────────────────────────────────

def test_fallback_when_server_unreachable():
    """存在しないエンドポイントへの接続失敗時にフォールバックすること。"""
    bad_llm = LLMAnalyzer(
        endpoint="http://127.0.0.1:19999",
        model="llama3.2:3b",
        timeout=2,
        fallback=True,
    )
    result = bad_llm.analyze("穏やかで認知症ケアに関心があります。夜勤対応可能。")
    assert result is not None
    assert result.features.mentioned_dementia is True
