"""Pure topology view model for the V1 UI shell."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ui.state_manager import mask_for_ui


@dataclass(frozen=True)
class TopologyViewer:
    """Display model for nodes, links, and topology evidence."""

    nodes: tuple[dict[str, Any], ...]
    links: tuple[dict[str, Any], ...]
    evidence_ids: tuple[str, ...]
    fidelity: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TopologyViewer":
        """Create a topology view from an externally produced mapping."""
        if not isinstance(payload, Mapping):
            raise ValueError("topology payload must be a mapping")
        nodes = tuple(dict(mask_for_ui(dict(item))) for item in payload.get("nodes", ()))
        links = tuple(dict(mask_for_ui(dict(item))) for item in payload.get("links", ()))
        return cls(nodes=nodes, links=links, evidence_ids=tuple(str(item) for item in payload.get("evidence_ids", ())), fidelity=str(payload.get("fidelity", "not_stated")))

    def render(self) -> dict[str, Any]:
        """Return a safe topology view model."""
        return {"nodes": [dict(item) for item in self.nodes], "links": [dict(item) for item in self.links], "evidence_ids": list(self.evidence_ids), "fidelity": self.fidelity}
