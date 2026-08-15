"""Traffic model registry and explicit link construction."""
from __future__ import annotations
from typing import Any, Mapping, Sequence
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import LinkType, TrafficData, TrafficLinkModel, TrafficSource

class TrafficModelRegistry:
    """Create and retain traffic link models from explicit inputs only."""
    def __init__(self) -> None:
        """Initialize the registry."""
        self.links: dict[str, TrafficLinkModel] = {}
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def create_link(self, *, link_id: str, source_device: str, source_interface: str, destination_device: str, destination_interface: str, link_speed_mbps: float, link_type: LinkType, traffic_data: TrafficData, users_served: int | None = None, devices_served: int | None = None, evidence_ids: Sequence[str] = (), assumptions: Sequence[str] = ()) -> TrafficLinkModel:
        """Create one link model and reject missing identity or capacity."""
        if not all([link_id, source_device, source_interface, destination_device, destination_interface]):
            raise ValueError("link identity fields are mandatory")
        if link_speed_mbps <= 0:
            raise ValueError("link_speed_mbps must be positive")
        if traffic_data.source == TrafficSource.COLLECTED and not traffic_data.evidence_ids:
            raise ValueError("collected traffic requires evidence_ids")
        link = TrafficLinkModel(link_id=link_id, source_device=source_device, source_interface=source_interface, destination_device=destination_device, destination_interface=destination_interface, link_speed_mbps=link_speed_mbps, link_type=link_type, traffic_data=traffic_data, users_served=users_served, devices_served=devices_served, evidence_ids=list(evidence_ids), assumptions=list(assumptions))
        self.links[link_id] = link
        decision = make_decision("TrafficModelRegistry", f"traffic-model:{link_id}", "accept_explicit_link", "accept only a link with explicit endpoints, speed, type, and traffic source", ["accept_explicit_link", "invent_missing_link_fields"], {"accept_explicit_link": "selected", "invent_missing_link_fields": "rejected"})
        self.decisions.append(decision)
        return link

    def get(self, link_id: str) -> TrafficLinkModel:
        """Return one link model."""
        if link_id not in self.links:
            raise KeyError(f"unknown traffic link: {link_id}")
        return self.links[link_id]

    def list(self) -> tuple[TrafficLinkModel, ...]:
        """Return links in insertion order."""
        return tuple(self.links.values())

    def record_assumption(self, key: str, value: Any, rationale: str) -> None:
        """Record a missing or estimated input."""
        self.assumptions.append(make_assumption(key, value, rationale, True))
