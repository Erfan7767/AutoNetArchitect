"""Tests for cross-specialty review aggregation and non-arbitrary conflict resolution."""

from site_agent.peer_review import (
    ConflictOption,
    ConflictResolutionState,
    PeerReviewFinding,
    PeerReviewState,
    ReviewSpecialty,
    build_engineering_review_report,
    resolve_conflict,
)


def _option(reference: str, eligible: bool) -> ConflictOption:
    return ConflictOption(
        option_reference=reference,
        evidence_references=(f"evidence://{reference}",),
        hard_constraints_satisfied=eligible,
        soft_constraint_summary="Declared trade-off only.",
        risk_summary="Human review records risk acceptance when needed.",
    )


def test_peer_review_report_preserves_blocker_and_human_action() -> None:
    report = build_engineering_review_report((
        PeerReviewFinding(
            specialty=ReviewSpecialty.ROUTING,
            decision_reference="decision://routing/01",
            state=PeerReviewState.PASSED,
            rationale="Observed platform evidence supports the reviewed design boundary.",
            evidence_references=("evidence://platform",),
        ),
        PeerReviewFinding(
            specialty=ReviewSpecialty.SECURITY,
            decision_reference="decision://security/01",
            state=PeerReviewState.BLOCKED,
            rationale="An authoritative security-policy reference is missing.",
            evidence_references=("evidence://missing-policy",),
            required_human_action="Provide approved security-policy evidence.",
        ),
    ))

    assert report.passed == 1
    assert report.blocked == 1
    assert report.release_permitted is False
    assert report.required_human_actions == ("Provide approved security-policy evidence.",)


def test_conflict_resolves_only_unique_hard_constraint_match() -> None:
    outcome = resolve_conflict((_option("option-a", True), _option("option-b", False)))

    assert outcome.state is ConflictResolutionState.RESOLVED_BY_HARD_CONSTRAINT
    assert outcome.selected_option_reference == "option-a"
    assert outcome.human_action_required is False


def test_conflict_with_multiple_eligible_options_requires_human_review() -> None:
    outcome = resolve_conflict((_option("option-a", True), _option("option-b", True)))

    assert outcome.state is ConflictResolutionState.HUMAN_REVIEW_REQUIRED
    assert outcome.selected_option_reference == ""
    assert outcome.human_action_required is True
