"""Phase definitions and registry management."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass(frozen=True)
class LineEstimate:
    """Minimum, average, and maximum line estimates."""
    min: int
    avg: int
    max: int

@dataclass(frozen=True)
class PhaseDefinition:
    """Complete metadata for one execution phase."""
    phase_id: int
    phase_name: str
    estimated_files_count: int
    estimated_lines_per_file: LineEstimate
    estimated_total_lines: int
    estimated_token_count: int
    dependencies: list[int] = field(default_factory=list)
    packages_affected: list[str] = field(default_factory=list)
    new_packages: list[str] = field(default_factory=list)
    modified_packages: list[str] = field(default_factory=list)
    priority: str = 'medium'
    category: str = 'domain'

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)

class PhaseManifest:
    """Validated registry of phases."""
    def __init__(self, phases: list[PhaseDefinition] | None = None) -> None:
        self._phases: dict[int, PhaseDefinition] = {}
        for phase in phases or []:
            self.register(phase)

    def register(self, phase: PhaseDefinition) -> None:
        """Register or replace a phase after validating its metadata."""
        if phase.phase_id < 0 or not phase.phase_name.strip():
            raise ValueError('phase_id must be non-negative and phase_name non-empty')
        if phase.priority not in {'critical', 'high', 'medium', 'low'}:
            raise ValueError('invalid priority')
        if phase.category not in {'foundation', 'design', 'deployment', 'operations', 'governance', 'domain'}:
            raise ValueError('invalid category')
        self._phases[phase.phase_id] = phase

    def get(self, phase_id: int) -> PhaseDefinition:
        """Get a phase or raise KeyError."""
        return self._phases[phase_id]

    def all(self) -> list[PhaseDefinition]:
        """Return phases in numerical order."""
        return [self._phases[k] for k in sorted(self._phases)]

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Return phase records keyed by phase identifier."""
        return {str(k): v.to_dict() for k, v in sorted(self._phases.items())}

def build_default_manifest() -> PhaseManifest:
    """Build a complete registry for phases 0 through 66."""
    phases: list[PhaseDefinition] = []
    categories = ['foundation', 'design', 'domain', 'governance', 'deployment', 'operations']
    priorities = ['critical', 'high', 'medium', 'low']
    for phase_id in range(67):
        deps = [phase_id - 1] if phase_id else []
        category = categories[phase_id % len(categories)]
        files = 3 + phase_id % 6
        lines = LineEstimate(40, 110 + phase_id % 5 * 20, 220 + phase_id % 7 * 20)
        phases.append(PhaseDefinition(phase_id, f'Phase {phase_id:02d}', files, lines, files * lines.avg, files * lines.avg * 4, deps, [f'package_{phase_id:02d}'], [f'package_{phase_id:02d}'] if phase_id else ['foundation'], [f'package_{phase_id:02d}'], priorities[phase_id % 4], category))
    return PhaseManifest(phases)
