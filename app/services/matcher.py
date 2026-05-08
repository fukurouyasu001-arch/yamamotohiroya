"""
マッチングオーケストレーター。
全事業所タイプにスコアを付けてランキングを生成する。
"""
from app.models.candidate import CandidateProfile
from app.models.facility import FacilityType, FacilityMatchResult, MatchingResponse, FACILITY_LABELS
from app.services.scorer import compute_score
from app.data.facility_profiles import FACILITY_TRAIT_PROFILES


def run_matching(profile: CandidateProfile) -> MatchingResponse:
    results: list[tuple[float, FacilityType, list[str], list[str]]] = []

    for facility_type in FacilityType:
        score, reasons, cautions = compute_score(profile, facility_type)
        results.append((score, facility_type, reasons, cautions))

    results.sort(key=lambda x: x[0], reverse=True)

    ranked = [
        FacilityMatchResult(
            facility_type=ft,
            label=FACILITY_LABELS[ft],
            score=score,
            rank=rank + 1,
            reasons=reasons,
            cautions=cautions,
        )
        for rank, (score, ft, reasons, cautions) in enumerate(results)
    ]

    top = ranked[0]
    summary = (
        f"{profile.candidate.name}さんには「{top.label}」が最も適合しています"
        f"（スコア: {top.score}/100）。"
        f"{FACILITY_TRAIT_PROFILES[top.facility_type]['description']}"
    )

    emotion = profile.video_analysis.emotion
    high_traits = [
        trait for trait, val in {
            "穏やかさ": emotion.calm,
            "共感力": emotion.empathy,
            "活動性": emotion.energy,
            "集中力": emotion.focus,
            "柔軟性": emotion.adaptability,
            "コミュニケーション力": emotion.communication,
        }.items() if val >= 0.7
    ]
    analysis_notes = (
        f"面接動画解析（信頼度: {profile.video_analysis.analysis_confidence:.0%}）より、"
        f"強みとして{'/'.join(high_traits) if high_traits else '全般的な特性'}が確認されました。"
    )

    return MatchingResponse(
        candidate_name=profile.candidate.name,
        recommended_facilities=ranked,
        summary=summary,
        analysis_notes=analysis_notes,
    )
