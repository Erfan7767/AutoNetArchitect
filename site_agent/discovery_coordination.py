"""Parallel coordination for explicitly authorized, read-only discovery work."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

from .agent import ReadOnlyCollector, ReadOnlyDiscoveryAgent
from .coordination import AgentAssignment, AgentRole, MultiAgentResponsibilityModel
from .models import DiscoveryResult, DiscoveryState, DiscoveryTarget
from .scope import AuthorizedScope

_COORDINATION_FAILURE_MESSAGE: Final[str] = (
    "The collector did not return evidence that can be safely bound to the approved target."
)


class DiscoveryWorkItem(BaseModel):
    """One immutable and secret-free discovery assignment for a local specialist."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    assignment: AgentAssignment
    target: DiscoveryTarget


class CoordinatedDiscoveryResult(BaseModel):
    """A discovery outcome with the agent and scope provenance needed for review."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    assignment: AgentAssignment
    result: DiscoveryResult
    scope_hash: str = Field(min_length=1, max_length=160)


class DiscoveryBatchResult(BaseModel):
    """Ordered batch outcome for an authorized parallel discovery operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    site_id: str = Field(min_length=1, max_length=160)
    scope_hash: str = Field(min_length=1, max_length=160)
    results: tuple[CoordinatedDiscoveryResult, ...]

    @property
    def has_unresolved_results(self) -> bool:
        """Return true whenever any target lacks verified discovered facts."""

        return any(item.result.state is not DiscoveryState.DISCOVERED for item in self.results)


@dataclass(frozen=True)
class ParallelDiscoveryCoordinator:
    """Coordinate bounded read-only collectors without granting release or execution authority."""

    scope: AuthorizedScope
    scope_hash: str
    collector: ReadOnlyCollector
    max_workers: int = 4

    def __post_init__(self) -> None:
        """Reject an invalid worker bound before any discovery work may begin."""

        if not self.scope_hash:
            raise ValueError("A non-empty approved scope hash is required.")
        if self.max_workers < 1:
            raise ValueError("At least one worker is required.")

    def run(self, work_items: tuple[DiscoveryWorkItem, ...]) -> DiscoveryBatchResult:
        """Run independent authorized targets concurrently and preserve input order.

        This method never creates targets, derives credentials, builds commands, or
        connects to an item whose assignment is not bound to this exact scope.
        """

        self._validate_batch(work_items)
        with ThreadPoolExecutor(max_workers=min(self.max_workers, max(1, len(work_items)))) as executor:
            futures: tuple[Future[CoordinatedDiscoveryResult], ...] = tuple(
                executor.submit(self._run_one, item) for item in work_items
            )
            results = tuple(future.result() for future in futures)
        return DiscoveryBatchResult(site_id=self.scope.site_id, scope_hash=self.scope_hash, results=results)

    def _validate_batch(self, work_items: tuple[DiscoveryWorkItem, ...]) -> None:
        """Reject duplicate assignment IDs and mismatched scope identities before dispatch."""

        assignment_ids = tuple(item.assignment.agent_id for item in work_items)
        if len(set(assignment_ids)) != len(assignment_ids):
            raise ValueError("Each discovery work item requires a distinct specialist assignment.")
        responsibility_model = MultiAgentResponsibilityModel()
        for item in work_items:
            if item.assignment.role is not AgentRole.AUTHORIZED_DISCOVERY:
                raise ValueError("Only authorized-discovery specialists may receive discovery work.")
            if not responsibility_model.assignment_matches_scope(item.assignment, self.scope.site_id, self.scope_hash):
                raise ValueError("Discovery work item assignment is not bound to the active approved scope.")

    def _run_one(self, item: DiscoveryWorkItem) -> CoordinatedDiscoveryResult:
        """Run one guarded collector and preserve a safe unresolved result on failure."""

        agent = ReadOnlyDiscoveryAgent(self.scope, self.collector)
        try:
            result = agent.discover(item.target)
        except (RuntimeError, TimeoutError, ValueError):
            result = DiscoveryResult(
                target=item.target,
                state=DiscoveryState.AMBIGUOUS,
                message=_COORDINATION_FAILURE_MESSAGE,
            )
        return CoordinatedDiscoveryResult(
            assignment=item.assignment,
            result=result,
            scope_hash=self.scope_hash,
        )
