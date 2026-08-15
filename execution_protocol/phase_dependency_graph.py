"""DAG construction and parallel phase analysis."""
from __future__ import annotations

class PhaseDependencyGraph:
    """Represent phase dependencies and calculate execution waves."""
    def __init__(self, dependencies: dict[int, list[int]]) -> None:
        self.dependencies = {int(k): set(v) for k, v in dependencies.items()}
    def validate(self) -> None:
        """Raise ValueError when a cycle exists or dependency is unknown."""
        nodes = set(self.dependencies)
        if any(dep not in nodes for deps in self.dependencies.values() for dep in deps): raise ValueError('unknown phase dependency')
        self._waves()
    def _waves(self) -> list[list[int]]:
        """Return topological execution waves."""
        remaining = {n: set(d) for n, d in self.dependencies.items()}; waves = []
        while remaining:
            ready = sorted(n for n, deps in remaining.items() if not deps)
            if not ready: raise ValueError('circular phase dependencies')
            waves.append(ready)
            for n in ready: remaining.pop(n)
            for deps in remaining.values(): deps.difference_update(ready)
        return waves
    def parallel_waves(self) -> list[list[int]]:
        """Return phases that may run concurrently."""
        self.validate(); return self._waves()
