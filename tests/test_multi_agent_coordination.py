"""Tests for the bounded multi-agent responsibility model."""

from site_agent.coordination import (
    AgentAssignment,
    AgentRole,
    CoordinationStage,
    MultiAgentResponsibilityModel,
)


def test_every_specialist_is_bounded_and_cannot_execute_production_changes() -> None:
    """Every defined specialist must have explicit outputs and no execution authority."""

    model = MultiAgentResponsibilityModel()

    for role in AgentRole:
        responsibility = model.responsibility_for(role)
        assert responsibility.required_inputs
        assert responsibility.required_outputs
        assert responsibility.prohibited_actions
        assert model.production_execution_permitted(role) is False


def test_handoff_order_requires_evidence_review_before_design_preparation() -> None:
    """The coordination order prevents direct discovery-to-design release behavior."""

    model = MultiAgentResponsibilityModel()

    assert model.stage_follows(CoordinationStage.DISCOVERY, CoordinationStage.EVIDENCE_REVIEW)
    assert not model.stage_follows(CoordinationStage.DISCOVERY, CoordinationStage.DESIGN_PREPARATION)
    assert model.stage_follows(CoordinationStage.SAFETY_REVIEW, CoordinationStage.HUMAN_GO_NO_GO)


def test_assignment_is_bound_to_exact_site_and_scope_hash() -> None:
    """An assignment cannot be reused for a different site or discovered scope."""

    model = MultiAgentResponsibilityModel()
    assignment = AgentAssignment(
        agent_id="discovery-specialist-1",
        role=AgentRole.AUTHORIZED_DISCOVERY,
        site_id="site-1",
        scope_hash="scope-abc",
        authority_reference="approval-1",
    )

    assert model.assignment_matches_scope(assignment, "site-1", "scope-abc")
    assert not model.assignment_matches_scope(assignment, "site-2", "scope-abc")
    assert not model.assignment_matches_scope(assignment, "site-1", "scope-other")

