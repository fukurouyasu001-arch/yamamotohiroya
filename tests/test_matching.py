"""
マッチングロジックの単体テスト（動画解析なし・モックデータ使用）。
"""
import pytest
from app.models.candidate import (
    CandidateInput, VideoAnalysisResult, EmotionProfile,
    SpeechProfile, CandidateProfile, WorkStyle, ShiftPreference,
)
from app.models.facility import FacilityType
from app.services.scorer import compute_score
from app.services.matcher import run_matching


def _make_profile(
    name="テスト太郎",
    work_style=WorkStyle.FULL_TIME,
    shift=ShiftPreference.NIGHT,
    calm=0.9, empathy=0.9, energy=0.5, focus=0.7,
    adaptability=0.6, communication=0.7,
    night_shift=True, dementia=True,
    disability=False, activity=False,
) -> CandidateProfile:
    emotion = EmotionProfile(
        calm=calm, empathy=empathy, energy=energy,
        focus=focus, adaptability=adaptability, communication=communication,
    )
    speech = SpeechProfile(
        transcript="夜勤も対応できます。認知症の方のケアに関心があります。",
        mentioned_night_shift=night_shift,
        mentioned_dementia=dementia,
        mentioned_disability=disability,
        mentioned_activity=activity,
        confidence_score=0.6,
    )
    candidate = CandidateInput(name=name, work_style=work_style, shift_preference=shift)
    video = VideoAnalysisResult(
        emotion=emotion, speech=speech,
        video_duration_seconds=300, analysis_confidence=0.85,
    )
    return CandidateProfile(candidate=candidate, video_analysis=video)


def test_group_home_scores_high_for_night_shift_dementia():
    profile = _make_profile(night_shift=True, dementia=True, shift=ShiftPreference.NIGHT)
    score, reasons, _ = compute_score(profile, FacilityType.GROUP_HOME)
    assert score > 60, f"グループホームスコアが低すぎます: {score}"
    assert any("夜勤" in r or "認知症" in r for r in reasons)


def test_day_service_scores_high_for_active_day():
    profile = _make_profile(
        energy=0.95, communication=0.9,
        shift=ShiftPreference.DAY,
        activity=True, night_shift=False, dementia=False,
    )
    score, reasons, _ = compute_score(profile, FacilityType.DAY_SERVICE)
    assert score > 55


def test_employment_support_scores_high_for_disability():
    profile = _make_profile(
        disability=True, shift=ShiftPreference.DAY,
        focus=0.9, night_shift=False, dementia=False,
    )
    score, _, _ = compute_score(profile, FacilityType.EMPLOYMENT_SUPPORT)
    assert score > 50


def test_matching_returns_all_facilities():
    profile = _make_profile()
    result = run_matching(profile)
    assert len(result.recommended_facilities) == len(FacilityType)
    ranks = [f.rank for f in result.recommended_facilities]
    assert ranks == sorted(ranks)


def test_matching_top_is_group_home_for_night_dementia():
    profile = _make_profile(night_shift=True, dementia=True, shift=ShiftPreference.NIGHT, calm=0.9, empathy=0.9)
    result = run_matching(profile)
    top = result.recommended_facilities[0]
    assert top.facility_type in (FacilityType.GROUP_HOME, FacilityType.SPECIAL_NURSING)


def test_small_scale_multi_rewards_adaptability():
    profile = _make_profile(
        adaptability=0.95, shift=ShiftPreference.FLEXIBLE,
        work_style=WorkStyle.FULL_TIME,
    )
    score, _, _ = compute_score(profile, FacilityType.SMALL_SCALE_MULTI)
    assert score > 55
