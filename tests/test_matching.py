"""
マッチングロジックおよび解析エンジンの単体テスト。
"""
import pytest
from app.models.candidate import (
    CandidateConditions, CandidateProfile, WorkStyle, ShiftPreference,
)
from app.models.facility import FacilityType
from app.services.analyzer import get_analyzer
from app.services.analyzer.keyword import KeywordAnalyzer
from app.services.analyzer.llm import LLMAnalyzer
from app.services.scorer import compute_score
from app.services.matcher import run_matching


# テスト全体で使う既定アナライザ（キーワード方式）
_analyzer = KeywordAnalyzer()


def _make_profile(
    name="テスト太郎",
    work_style=WorkStyle.FULL_TIME,
    shift=ShiftPreference.NIGHT,
    interview_text="",
) -> CandidateProfile:
    candidate = CandidateConditions(name=name, work_style=work_style, shift_preference=shift)
    analysis = _analyzer.analyze(interview_text)
    return CandidateProfile(candidate=candidate, analysis=analysis)


# ── ファクトリ ────────────────────────────────────

def test_factory_returns_keyword_analyzer_by_default():
    analyzer = get_analyzer()
    assert analyzer.name == "keyword"


def test_llm_analyzer_raises_not_implemented():
    llm = LLMAnalyzer(endpoint="http://localhost:11434", model="dummy", timeout=30)
    with pytest.raises(NotImplementedError):
        llm.analyze("テスト")


# ── KeywordAnalyzer ───────────────────────────────

def test_calm_trait_extracted_from_text():
    result = _analyzer.analyze("穏やかで落ち着いた対応が得意です。冷静に判断できます。")
    assert result.trait.calm >= 0.5


def test_empathy_trait_extracted():
    result = _analyzer.analyze("ご利用者に寄り添い共感を大切にしています。傾聴を心がけています。")
    assert result.trait.empathy >= 0.5


def test_night_shift_flag_detected():
    result = _analyzer.analyze("夜勤も積極的に入りたいと考えています。夜間の対応に慣れています。")
    assert result.features.mentioned_night_shift is True


def test_dementia_flag_detected():
    result = _analyzer.analyze("認知症の方のケアに関心があります。認知機能の低下に寄り添いたい。")
    assert result.features.mentioned_dementia is True


def test_disability_flag_detected():
    result = _analyzer.analyze("就労支援B型で障害のある方の支援をしていました。")
    assert result.features.mentioned_disability is True


def test_activity_flag_detected():
    result = _analyzer.analyze("レクリエーションや体操など活動支援が好きです。")
    assert result.features.mentioned_activity is True


def test_experience_years_extracted():
    result = _analyzer.analyze("介護の仕事を5年続けてきました。")
    assert result.features.experience_years == 5


def test_empty_text_returns_low_confidence():
    result = _analyzer.analyze("")
    assert result.analysis_confidence < 0.3


# ── scorer ────────────────────────────────────────

def test_group_home_scores_high_for_night_shift_dementia():
    text = "穏やかで夜勤も対応できます。認知症の祖母を介護した経験があります。共同生活の支援に関心があります。"
    profile = _make_profile(shift=ShiftPreference.NIGHT, interview_text=text)
    score, reasons, _ = compute_score(profile, FacilityType.GROUP_HOME)
    assert score > 55
    assert len(reasons) > 0


def test_day_service_scores_high_for_energetic_activity():
    text = "明るく積極的に活動支援をしてきました。レクリエーションや体操が得意です。元気よく利用者と関わります。"
    profile = _make_profile(shift=ShiftPreference.DAY, interview_text=text)
    score, _, _ = compute_score(profile, FacilityType.DAY_SERVICE)
    assert score > 50


def test_employment_support_scores_high_for_disability():
    text = "障害のある方の就労支援に携わってきました。精神障害や知的障害の方への支援経験があります。責任感を持って取り組みます。"
    profile = _make_profile(shift=ShiftPreference.DAY, interview_text=text)
    score, _, _ = compute_score(profile, FacilityType.EMPLOYMENT_SUPPORT)
    assert score > 50


def test_small_scale_multi_rewards_flexibility():
    text = (
        "柔軟に対応できます。臨機応変に動くことが得意で、幅広い業務をこなしてきました。"
        "穏やかで落ち着いた対応を心がけており、状況に応じた判断が得意です。"
        "コミュニケーションを大切にしてチームワークで動いてきました。"
    )
    profile = _make_profile(shift=ShiftPreference.FLEXIBLE, interview_text=text)
    score, _, _ = compute_score(profile, FacilityType.SMALL_SCALE_MULTI)
    assert score > 50


# ── matcher ───────────────────────────────────────

def test_matching_returns_all_facilities():
    profile = _make_profile(interview_text="介護の仕事に意欲があります。")
    result = run_matching(profile)
    assert len(result.recommended_facilities) == len(FacilityType)
    ranks = [f.rank for f in result.recommended_facilities]
    assert ranks == sorted(ranks)


def test_matching_top_score_is_highest():
    profile = _make_profile(interview_text="穏やかで夜勤可。認知症ケアに強い関心があります。")
    result = run_matching(profile)
    scores = [f.score for f in result.recommended_facilities]
    assert scores[0] == max(scores)


def test_matching_summary_contains_candidate_name():
    profile = _make_profile(name="山田花子", interview_text="共感力があり傾聴を大切にしています。")
    result = run_matching(profile)
    assert "山田花子" in result.summary
