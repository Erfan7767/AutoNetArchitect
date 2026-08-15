"""Split phases into self-contained prompts while keeping model tests together."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .phase_manifest import PhaseManifest

@dataclass
class SubPrompt:
    """A bounded unit of phase execution."""
    sub_prompt_id: str
    parent_phase_id: int
    files_included: list[str]
    estimated_tokens: int
    context_requirements: list[str] = field(default_factory=list)
    imports_from_previous_subs: list[str] = field(default_factory=list)
    outputs_consumed_by_next_subs: list[str] = field(default_factory=list)
    send_order: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize the sub-prompt."""
        return self.__dict__.copy()

class PhaseSubdivider:
    """Create ordered sub-prompts from a phase file list."""
    def __init__(self, manifest: PhaseManifest, max_tokens: int = 12000) -> None:
        self.manifest, self.max_tokens = manifest, max_tokens

    def subdivide(self, phase_id: int, files: list[str], file_tokens: dict[str, int] | None = None) -> list[SubPrompt]:
        """Partition files without separating a model from its matching test."""
        self.manifest.get(phase_id)
        costs = file_tokens or {path: 500 for path in files}
        groups: list[list[str]] = []
        for path in files:
            stem = path.rsplit('/', 1)[-1].replace('.py', '')
            paired = next((g for g in groups if any(stem.startswith('test_') and x.endswith(stem[5:] + '.py') for x in g)), None)
            if paired is not None:
                paired.append(path); continue
            if groups and sum(costs.get(x, 500) for x in groups[-1]) + costs.get(path, 500) <= self.max_tokens:
                groups[-1].append(path)
            else:
                groups.append([path])
        return [SubPrompt(f'{phase_id}.{i}', phase_id, group, sum(costs.get(x, 500) for x in group), ['manifest metadata'], [], [], i) for i, group in enumerate(groups, 1)]
