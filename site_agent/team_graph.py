"""Evidence-first scheduling model for the supervised AutoNetArchitect agent team."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .coordination import AgentRole, MultiAgentResponsibilityModel


class TeamAgentState(str, Enum):
    """Non-authorizing state assigned to each specialist in a workflow evaluation."""

    READY = "ready"
    WAITING = "waiting"
    BLOCKED = "blocked"
    ABSTAINED = "abstained"
    COMPLETED = "completed"


class TeamAgentNode(BaseModel):
    """Machine-readable responsibility, dependencies, and scheduling boundary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: AgentRole
    dependency_roles: tuple[AgentRole, ...]
    required_evidence: tuple[str, ...] = Field(min_length=1)
    parallelization_boundary: str = Field(min_length=1, max_length=300)
    prohibited_actions: tuple[str, ...] = Field(min_length=1)


class TeamAgentStatus(BaseModel):
    """Result for one graph node, preserving missing evidence as an explicit blocker."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: AgentRole
    state: TeamAgentState
    blockers: tuple[str, ...] = ()


class TeamGraphEvaluation(BaseModel):
    """Full team status without any release, upload, or execution authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agents: tuple[TeamAgentStatus, ...]
    parallel_ready_roles: tuple[AgentRole, ...]
    production_execution_permitted: bool = False
    production_execution_reason: str = "No agent role may configure or execute a production device."

    def audit_details(self) -> dict[str, object]:
        """Return secret-free workflow evidence suitable for an immutable audit event."""

        return {
            "production_execution_permitted": self.production_execution_permitted,
            "production_execution_reason": self.production_execution_reason,
            "agents": [
                {"role": status.role.value, "state": status.state.value, "blockers": status.blockers}
                for status in self.agents
            ],
        }


class MultiAgentTeamGraph:
    """Schedule evidence-ready work while making unmet dependencies non-bypassable."""

    _DEPENDENCIES: dict[AgentRole, tuple[AgentRole, ...]] = {
        AgentRole.AUTHORIZED_DISCOVERY: (),
        AgentRole.EVIDENCE_REVIEW: (AgentRole.AUTHORIZED_DISCOVERY,),
        AgentRole.DESIGN_PREPARATION: (AgentRole.EVIDENCE_REVIEW,),
        AgentRole.CAPABILITY_ASSESSMENT: (AgentRole.DESIGN_PREPARATION,),
        AgentRole.VIRTUAL_VALIDATION: (AgentRole.CAPABILITY_ASSESSMENT,),
        AgentRole.SAFETY_REVIEW: (AgentRole.VIRTUAL_VALIDATION,),
        AgentRole.RELEASE_COORDINATION: (AgentRole.SAFETY_REVIEW,),
    }

    def __init__(self, responsibilities: MultiAgentResponsibilityModel | None = None) -> None:
        self._responsibilities = responsibilities or MultiAgentResponsibilityModel()

    def manifest(self) -> tuple[TeamAgentNode, ...]:
        """Return all currently bounded specialists and their declared dependencies."""

        return tuple(
            TeamAgentNode(
                role=role,
                dependency_roles=self._DEPENDENCIES[role],
                required_evidence=self._responsibilities.responsibility_for(role).required_inputs,
                parallelization_boundary=(
                    "Only independent approved discovery targets may run concurrently; no device modification is permitted."
                    if role is AgentRole.AUTHORIZED_DISCOVERY
                    else "This role may run only after its declared predecessor evidence is complete."
                ),
                prohibited_actions=self._responsibilities.responsibility_for(role).prohibited_actions,
            )
            for role in AgentRole
        )

    def evaluate(
        self,
        evidence_keys: frozenset[str],
        completed_roles: frozenset[AgentRole] = frozenset(),
        blocked_roles: frozenset[AgentRole] = frozenset(),
    ) -> TeamGraphEvaluation:
        """Return ready work and explicit blockers from evidence and predecessor states."""

        statuses: list[TeamAgentStatus] = []
        for node in self.manifest():
            if node.role in completed_roles:
                statuses.append(TeamAgentStatus(role=node.role, state=TeamAgentState.COMPLETED))
                continue
            missing_dependencies = tuple(role for role in node.dependency_roles if role not in completed_roles)
            missing_evidence = tuple(key for key in node.required_evidence if key not in evidence_keys)
            if node.role in blocked_roles:
                statuses.append(TeamAgentStatus(role=node.role, state=TeamAgentState.BLOCKED, blockers=("A prior agent outcome is unresolved, unsupported, or explicitly blocked.",)))
            elif missing_dependencies:
                statuses.append(TeamAgentStatus(role=node.role, state=TeamAgentState.WAITING, blockers=tuple(f"Requires completed {role.value}." for role in missing_dependencies)))
            elif missing_evidence:
                statuses.append(TeamAgentStatus(role=node.role, state=TeamAgentState.ABSTAINED, blockers=tuple(f"Missing required evidence: {key}." for key in missing_evidence)))
            else:
                statuses.append(TeamAgentStatus(role=node.role, state=TeamAgentState.READY))
        return TeamGraphEvaluation(
            agents=tuple(statuses),
            parallel_ready_roles=tuple(status.role for status in statuses if status.state is TeamAgentState.READY),
        )
