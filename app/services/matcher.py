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

    trait = profile.analysis.trait
    high_traits = [
        label for label, val in {
            "穏やかさ": trait.calm,
            "共感力": trait.empathy,
            "活動性": trait.energy,
            "集中力": trait.focus,
            "柔軟性": trait.adaptability,
            "コミュニケーション力": trait.communication,
        }.items() if val >= 0.6
    ]
    analysis_notes = (
        f"面接テキスト解析（信頼度: {profile.analysis.analysis_confidence:.0%}）より、"
        f"強みとして{'/'.join(high_traits) if high_traits else '全般的な特性'}が確認されました。"
    )

    return MatchingResponse(
        candidate_name=profile.candidate.name,
        recommended_facilities=ranked,
        summary=summary,
        analysis_notes=analysis_notes,
    )
