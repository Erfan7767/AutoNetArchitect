"""Allocate remaining phases across conversations."""
from __future__ import annotations
from dataclasses import dataclass
from .phase_dependency_graph import PhaseDependencyGraph

@dataclass(frozen=True)
class ConversationPlan:
    """Conversation allocation and checkpoint plan."""
    conversations: list[list[int]]
    handoff_points: list[int]
    validation_checkpoints: list[int]

class ConversationPlanner:
    """Plan conversations from a dependency graph and capacity."""
    def plan(self, remaining: list[int], dependencies: dict[int, list[int]], capacity: int = 5) -> ConversationPlan:
        """Group topological waves into bounded conversations."""
        graph = PhaseDependencyGraph({i: dependencies.get(i, []) for i in remaining}); waves = graph.parallel_waves(); groups: list[list[int]] = []
        for wave in waves:
            for i in range(0, len(wave), capacity): groups.append(wave[i:i+capacity])
        return ConversationPlan(groups, [g[-1] for g in groups[:-1]], [g[-1] for g in groups])
