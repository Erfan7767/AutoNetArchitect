"""Cross-specialty peer review and deterministic conflict handling for engineering evidence."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ReviewSpecialty(str, Enum):
    """Disciplines that can independently review an engineering decision."""

    ARCHITECTURE = "architecture"
    ROUTING = "routing"
    SECURITY = "security"
    ADDRESSING = "addressing"
    LAYER2 = "layer2"
    EQUIPMENT = "equipment"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"


class PeerReviewState(str, Enum):
    """Bounded outcomes for a specialist review."""

    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"


class PeerReviewFinding(BaseModel):
    """A traceable, non-authorizing review finding for an engineering decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    specialty: ReviewSpecialty
    decision_reference: str = Field(min_length=1, max_length=200)
    state: PeerReviewState
    rationale: str = Field(min_length=1, max_length=1000)
    evidence_references: tuple[str, ...] = Field(min_length=1)
    alternatives_considered: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    required_human_action: str = Field(default="", max_length=500)


class ConflictOption(BaseModel):
    """An evidence-backed candidate that can be resolved only by declared hard constraints."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    option_reference: str = Field(min_length=1, max_length=200)
    evidence_references: tuple[str, ...] = Field(min_length=1)
    hard_constraints_satisfied: bool
    soft_constraint_summary: str = Field(min_length=1, max_length=500)
    risk_summary: str = Field(min_length=1, max_length=500)


class ConflictResolutionState(str, Enum):
    """Explicit result of a conflict evaluation without silently choosing a design."""

    RESOLVED_BY_HARD_CONSTRAINT = "resolved_by_hard_constraint"
    DEFERRED = "deferred"
    HUMAN_REVIEW_REQUIRED = "human_review_required"


class ConflictResolution(BaseModel):
    """Traceable conflict outcome preserving all alternatives for review."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    state: ConflictResolutionState
    selected_option_reference: str = Field(default="", max_length=200)
    alternatives: tuple[ConflictOption, ...]
    rationale: str = Field(min_length=1, max_length=1000)
    human_action_required: bool


class EngineeringReviewReport(BaseModel):
    """Aggregates peer findings without making release or execution decisions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    findings: tuple[PeerReviewFinding, ...] = Field(min_length=1)
    passed: int
    failed: int
    blocked: int
    unresolved: int
    required_human_actions: tuple[str, ...]
    release_permitted: bool = False
    release_reason: str = "Peer review is advisory evidence; release requires separate human approval readiness."


def build_engineering_review_report(findings: tuple[PeerReviewFinding, ...]) -> EngineeringReviewReport:
    """Aggregate declared review findings while keeping unresolved work explicitly visible."""

    if not findings:
        raise ValueError("At least one peer-review finding is required")
    actions = tuple(
        finding.required_human_action
        for finding in findings
        if finding.required_human_action
    )
    return EngineeringReviewReport(
        findings=findings,
        passed=sum(finding.state is PeerReviewState.PASSED for finding in findings),
        failed=sum(finding.state is PeerReviewState.FAILED for finding in findings),
        blocked=sum(finding.state is PeerReviewState.BLOCKED for finding in findings),
        unresolved=sum(finding.state is PeerReviewState.UNRESOLVED for finding in findings),
        required_human_actions=actions,
    )


def resolve_conflict(options: tuple[ConflictOption, ...]) -> ConflictResolution:
    """Resolve only a uniquely hard-constraint-compliant option; otherwise defer or escalate."""

    if not options:
        raise ValueError("At least one conflict option is required")
    eligible = tuple(option for option in options if option.hard_constraints_satisfied)
    if len(eligible) == 1:
        return ConflictResolution(
            state=ConflictResolutionState.RESOLVED_BY_HARD_CONSTRAINT,
            selected_option_reference=eligible[0].option_reference,
            alternatives=options,
            rationale="Exactly one option satisfies the declared hard constraints; no soft-score assumption was used.",
            human_action_required=False,
        )
    if not eligible:
        return ConflictResolution(
            state=ConflictResolutionState.DEFERRED,
            alternatives=options,
            rationale="No option satisfies all declared hard constraints; the decision remains deferred.",
            human_action_required=True,
        )
    return ConflictResolution(
        state=ConflictResolutionState.HUMAN_REVIEW_REQUIRED,
        alternatives=options,
        rationale="Multiple options satisfy hard constraints; trade-offs require named human engineering review.",
        human_action_required=True,
    )
