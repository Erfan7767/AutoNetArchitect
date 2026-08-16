"""Tests for the dependency-bound multi-agent team scheduler."""

from site_agent.coordination import AgentAssignment, AgentRole
from site_agent.discovery_coordination import DiscoveryWorkItem, ParallelDiscoveryCoordinator
from site_agent.models import DiscoveryResult, DiscoveryState, DiscoveryTarget, ManagementProtocol, ObservedDeviceFacts
from site_agent.scope import AuthorizedScope
from site_agent.team_graph import MultiAgentTeamGraph, TeamAgentState


def _status_by_role(graph_result: object, role: AgentRole) -> object:
    return next(status for status in graph_result.agents if status.role is role)


def test_manifest_covers_every_bounded_agent_and_preserves_prohibitions() -> None:
    graph = MultiAgentTeamGraph()

    manifest = graph.manifest()

    assert {node.role for node in manifest} == set(AgentRole)
    assert all(node.prohibited_actions for node in manifest)
    assert "Only independent approved discovery targets" in manifest[0].parallelization_boundary


def test_graph_schedules_only_authorized_discovery_until_evidence_and_dependencies_arrive() -> None:
    graph = MultiAgentTeamGraph()
    evidence = frozenset({"approved_scope", "target", "protocol", "credential_reference"})

    result = graph.evaluate(evidence)

    assert _status_by_role(result, AgentRole.AUTHORIZED_DISCOVERY).state is TeamAgentState.READY
    assert _status_by_role(result, AgentRole.EVIDENCE_REVIEW).state is TeamAgentState.WAITING
    assert result.parallel_ready_roles == (AgentRole.AUTHORIZED_DISCOVERY,)


def test_graph_abstains_from_capability_work_without_license_evidence() -> None:
    graph = MultiAgentTeamGraph()
    result = graph.evaluate(
        frozenset({"observed_platform", "software_version", "design_artifact"}),
        completed_roles=frozenset({AgentRole.AUTHORIZED_DISCOVERY, AgentRole.EVIDENCE_REVIEW, AgentRole.DESIGN_PREPARATION}),
    )

    capability = _status_by_role(result, AgentRole.CAPABILITY_ASSESSMENT)
    assert capability.state is TeamAgentState.ABSTAINED
    assert capability.blockers == ("Missing required evidence: license_evidence.",)


def test_graph_distinguishes_waiting_policy_block_and_abstention() -> None:
    graph = MultiAgentTeamGraph()
    result = graph.evaluate(
        frozenset({"approved_scope", "target", "protocol", "credential_reference"}),
        blocked_roles=frozenset({AgentRole.SAFETY_REVIEW}),
    )

    assert _status_by_role(result, AgentRole.EVIDENCE_REVIEW).state is TeamAgentState.WAITING
    assert _status_by_role(result, AgentRole.SAFETY_REVIEW).state is TeamAgentState.BLOCKED
    assert _status_by_role(result, AgentRole.AUTHORIZED_DISCOVERY).state is TeamAgentState.READY


def test_full_team_dependency_chain_releases_only_the_next_evidence_ready_role() -> None:
    graph = MultiAgentTeamGraph()
    all_evidence = frozenset({key for node in graph.manifest() for key in node.required_evidence})
    completed: set[AgentRole] = set()

    for node in graph.manifest():
        result = graph.evaluate(all_evidence, completed_roles=frozenset(completed))
        assert _status_by_role(result, node.role).state is TeamAgentState.READY
        later = [candidate.role for candidate in graph.manifest() if candidate.role not in completed and candidate.role is not node.role]
        if later:
            assert _status_by_role(result, later[0]).state is TeamAgentState.WAITING
        completed.add(node.role)

    final = graph.evaluate(all_evidence, completed_roles=frozenset(completed))
    assert all(status.state is TeamAgentState.COMPLETED for status in final.agents)
    assert final.production_execution_permitted is False


def test_graph_ready_discovery_dispatches_parallel_authorized_targets_only() -> None:
    graph = MultiAgentTeamGraph()
    graph_result = graph.evaluate(frozenset({"approved_scope", "target", "protocol", "credential_reference"}))
    assert _status_by_role(graph_result, AgentRole.AUTHORIZED_DISCOVERY).state is TeamAgentState.READY
    assert _status_by_role(graph_result, AgentRole.EVIDENCE_REVIEW).state is TeamAgentState.WAITING

    scope = AuthorizedScope(
        site_id="site-1",
        approved_networks=("10.0.0.0/24",),
        approved_targets=("10.0.0.10", "10.0.0.11"),
        allowed_protocols=(ManagementProtocol.HTTPS_API,),
        approval_reference="approval-1",
        operator_acknowledged=True,
    )
    items = tuple(
        DiscoveryWorkItem(
            assignment=AgentAssignment(agent_id=f"agent-{index}", role=AgentRole.AUTHORIZED_DISCOVERY, site_id="site-1", scope_hash="scope-1", authority_reference="approval-1"),
            target=DiscoveryTarget(address=address, protocol=ManagementProtocol.HTTPS_API, credential_reference=f"credential-{index}"),
        )
        for index, address in enumerate(("10.0.0.10", "10.0.0.11"), start=1)
    )

    def collector(target: DiscoveryTarget) -> DiscoveryResult:
        return DiscoveryResult(
            target=target,
            state=DiscoveryState.DISCOVERED,
            facts=ObservedDeviceFacts(vendor="Cisco", platform="Catalyst", software_version="17.18.1", serial_reference="redacted", interface_count=24),
            message="Read-only observed evidence.",
        )

    result = ParallelDiscoveryCoordinator(scope, "scope-1", collector, max_workers=2).run(items)
    assert len(result.results) == 2
    assert not result.has_unresolved_results

    after_discovery = graph.evaluate(
        frozenset({"approved_scope", "target", "protocol", "credential_reference", "discovery_result", "evidence_provenance"}),
        completed_roles=frozenset({AgentRole.AUTHORIZED_DISCOVERY}),
    )
    assert _status_by_role(after_discovery, AgentRole.EVIDENCE_REVIEW).state is TeamAgentState.READY
    assert _status_by_role(after_discovery, AgentRole.DESIGN_PREPARATION).state is TeamAgentState.WAITING
    assert after_discovery.production_execution_permitted is False


def test_graph_never_permits_production_execution() -> None:
    graph = MultiAgentTeamGraph()
    completed = frozenset(AgentRole)

    result = graph.evaluate(frozenset({key for node in graph.manifest() for key in node.required_evidence}), completed)

    assert result.production_execution_permitted is False
    assert "No agent role" in result.production_execution_reason


def test_audit_details_preserve_states_without_input_references() -> None:
    graph = MultiAgentTeamGraph()
    result = graph.evaluate(frozenset({"approved_scope", "target", "protocol", "credential_reference"}))

    details = result.audit_details()

    assert details["production_execution_permitted"] is False
    assert "credential_reference" not in str(details)
    assert any(agent["role"] == AgentRole.AUTHORIZED_DISCOVERY.value for agent in details["agents"])
