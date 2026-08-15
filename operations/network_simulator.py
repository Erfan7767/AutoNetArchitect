"""Logical network simulation bounded away from protocol emulation and production claims."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class SimulationStatus(str, Enum):
    """Outcomes for logical simulation and resilience analysis."""

    COMPLETED = "completed"
    BLOCKED_MISSING_HUMAN_DATA = "blocked_missing_human_data"
    NOT_VERIFIABLE = "not_verifiable_with_current_inputs"
    FAILED = "failed"


class ResilienceStatus(str, Enum):
    """Logical resilience outcomes."""

    RESILIENT = "resilient"
    DEGRADED = "degraded"
    NOT_RESILIENT = "not_resilient"
    NOT_VERIFIABLE = "not_verifiable_with_current_inputs"


@dataclass(frozen=True)
class SimulationEvent:
    """One logical fault or state transition applied to a model."""

    event_id: str
    event_type: str
    target: str
    status: str
    detail: str
    affected_nodes: tuple[str, ...] = ()
    affected_links: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize an event."""
        return asdict(self) | {"affected_nodes": list(self.affected_nodes), "affected_links": list(self.affected_links)}


@dataclass(frozen=True)
class ResilienceAnalysis:
    """Logical resilience result with explicit limitations."""

    scenario_id: str
    status: str
    failed_components: tuple[str, ...]
    surviving_paths: tuple[str, ...]
    lost_paths: tuple[str, ...]
    unknown_paths: tuple[str, ...]
    assumptions: tuple[str, ...]
    production_claim_allowed: bool = False
    limitation: str = "logical connectivity only; simulator evidence is insufficient for production safety"

    def to_dict(self) -> dict[str, Any]:
        """Serialize resilience analysis."""
        return asdict(self) | {"failed_components": list(self.failed_components), "surviving_paths": list(self.surviving_paths), "lost_paths": list(self.lost_paths), "unknown_paths": list(self.unknown_paths), "assumptions": list(self.assumptions)}


@dataclass(frozen=True)
class SimulationResult:
    """Complete logical simulation result, never a production proof."""

    simulation_id: str
    status: str
    simulator_kind: str
    protocol_emulation: bool
    production_claim_allowed: bool
    initial_state: dict[str, Any]
    final_state: dict[str, Any]
    events: tuple[SimulationEvent, ...]
    path_results: dict[str, str]
    assumptions: tuple[str, ...]
    resilience: tuple[ResilienceAnalysis, ...] = ()
    limitations: tuple[str, ...] = ("logical model only", "does not validate vendor protocol behavior", "does not authorize production change")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the simulation result."""
        return {
            "simulation_id": self.simulation_id,
            "status": self.status,
            "simulator_kind": self.simulator_kind,
            "protocol_emulation": self.protocol_emulation,
            "production_claim_allowed": self.production_claim_allowed,
            "initial_state": self.initial_state,
            "final_state": self.final_state,
            "events": [event.to_dict() for event in self.events],
            "path_results": dict(self.path_results),
            "assumptions": list(self.assumptions),
            "resilience": [item.to_dict() for item in self.resilience],
            "limitations": list(self.limitations),
        }


class NetworkSimulator:
    """Run deterministic graph-based logical simulations only.

    The simulator models node/link availability and declared reachability intents.
    It does not model vendor protocol state machines, timing, packet behavior,
    convergence, hardware faults, or physical conditions.
    """

    SIMULATOR_KIND = "logical_network_simulator"

    def simulate(
        self,
        topology: Mapping[str, Any] | None,
        reachability_intents: Mapping[str, Mapping[str, Any]] | None,
        events: Sequence[Mapping[str, Any]] = (),
        resilience_scenarios: Sequence[Mapping[str, Any]] = (),
    ) -> SimulationResult:
        """Apply declared logical events and evaluate declared reachability intents."""
        normalized = self._normalize_topology(topology)
        if normalized is None or not reachability_intents:
            return self._blocked("topology and reachability_intents are required")
        nodes, links = normalized
        initial_state = {"nodes": {name: dict(value) for name, value in nodes.items()}, "links": {link_id: dict(value) for link_id, value in links.items()}}
        current_nodes = {name: dict(value) for name, value in nodes.items()}
        current_links = {link_id: dict(value) for link_id, value in links.items()}
        event_results: list[SimulationEvent] = []
        assumptions: list[str] = ["node and link state are interpreted only when explicitly declared", "logical graph reachability is not a protocol behavior proof"]
        for index, raw_event in enumerate(events, start=1):
            event = self._apply_event(index, raw_event, current_nodes, current_links)
            event_results.append(event)
            if event.status != "applied":
                assumptions.append(f"event {event.event_id} could not be applied without additional human data")
        path_results = self._evaluate_paths(current_nodes, current_links, reachability_intents)
        status = SimulationStatus.COMPLETED.value if all(value in {"verified", "failed"} for value in path_results.values()) and not any(event.status != "applied" for event in event_results) else SimulationStatus.NOT_VERIFIABLE.value
        resilience = tuple(self.analyze_resilience({"nodes": tuple(current_nodes.values()), "links": tuple(current_links.values())}, reachability_intents, resilience_scenarios)) if resilience_scenarios else ()
        if any(item.status == ResilienceStatus.NOT_RESILIENT.value for item in resilience):
            status = SimulationStatus.FAILED.value
        return SimulationResult("logical-simulation", status, self.SIMULATOR_KIND, False, False, initial_state, {"nodes": current_nodes, "links": current_links}, tuple(event_results), path_results, tuple(dict.fromkeys(assumptions)), resilience)

    def analyze_resilience(
        self,
        topology: Mapping[str, Any] | None,
        reachability_intents: Mapping[str, Mapping[str, Any]] | None,
        scenarios: Sequence[Mapping[str, Any]] | None,
    ) -> tuple[ResilienceAnalysis, ...]:
        """Evaluate declared failure scenarios against logical reachability only."""
        normalized = self._normalize_topology(topology)
        if normalized is None or not reachability_intents or not scenarios:
            return (ResilienceAnalysis("resilience:blocked", ResilienceStatus.NOT_VERIFIABLE.value, (), (), (), tuple(reachability_intents or ()), ("topology, intents, and scenarios are required",)),)
        results: list[ResilienceAnalysis] = []
        nodes, links = normalized
        for index, scenario in enumerate(scenarios, start=1):
            scenario_id = str(scenario.get("scenario_id", f"scenario-{index}"))
            event = scenario.get("event", scenario)
            scenario_nodes = {name: dict(value) for name, value in nodes.items()}
            scenario_links = {link_id: dict(value) for link_id, value in links.items()}
            applied = self._apply_event(index, event if isinstance(event, Mapping) else {}, scenario_nodes, scenario_links)
            if applied.status != "applied":
                results.append(ResilienceAnalysis(scenario_id, ResilienceStatus.NOT_VERIFIABLE.value, (), (), (), tuple(str(key) for key in reachability_intents), ("failure scenario is incomplete or references an unknown component",)))
                continue
            path_results = self._evaluate_paths(scenario_nodes, scenario_links, reachability_intents)
            surviving = tuple(path_id for path_id, result in path_results.items() if result == "verified")
            lost = tuple(path_id for path_id, result in path_results.items() if result == "failed")
            unknown = tuple(path_id for path_id, result in path_results.items() if result not in {"verified", "failed"})
            if unknown:
                resilience_status = ResilienceStatus.NOT_VERIFIABLE.value
            elif lost and surviving:
                resilience_status = ResilienceStatus.DEGRADED.value
            elif lost:
                resilience_status = ResilienceStatus.NOT_RESILIENT.value
            else:
                resilience_status = ResilienceStatus.RESILIENT.value
            results.append(ResilienceAnalysis(scenario_id, resilience_status, tuple(item for item in (applied.affected_nodes + applied.affected_links)), surviving, lost, unknown, ("resilience result is derived from the declared logical graph",)))
        return tuple(results)

    @staticmethod
    def _normalize_topology(topology: Mapping[str, Any] | None) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]] | None:
        """Normalize nodes and links without generating missing state or identifiers."""
        if not isinstance(topology, Mapping) or not topology.get("nodes") or not topology.get("links"):
            return None
        nodes: dict[str, dict[str, Any]] = {}
        for raw in topology["nodes"]:
            if not isinstance(raw, Mapping) or not raw.get("name"):
                return None
            nodes[str(raw["name"])] = dict(raw)
        links: dict[str, dict[str, Any]] = {}
        for index, raw in enumerate(topology["links"], start=1):
            if not isinstance(raw, Mapping) or not raw.get("source") or not raw.get("target"):
                return None
            link_id = str(raw.get("link_id", f"link-{index}"))
            links[link_id] = dict(raw) | {"link_id": link_id}
        return nodes, links

    @staticmethod
    def _apply_event(index: int, raw_event: Mapping[str, Any], nodes: dict[str, dict[str, Any]], links: dict[str, dict[str, Any]]) -> SimulationEvent:
        """Apply a bounded logical event to a copy of the graph."""
        event_id = str(raw_event.get("event_id", f"event-{index}"))
        event_type = str(raw_event.get("event_type", raw_event.get("type", ""))).lower()
        target = str(raw_event.get("target", ""))
        if event_type in {"disable_node", "node_down"}:
            if target not in nodes:
                return SimulationEvent(event_id, event_type, target, "unknown_target", "node target is not present in topology")
            nodes[target]["state"] = "down"
            return SimulationEvent(event_id, event_type, target, "applied", "node logically disabled", (target,), ())
        if event_type in {"enable_node", "node_up"}:
            if target not in nodes:
                return SimulationEvent(event_id, event_type, target, "unknown_target", "node target is not present in topology")
            nodes[target]["state"] = "up"
            return SimulationEvent(event_id, event_type, target, "applied", "node logically enabled", (target,), ())
        if event_type in {"disable_link", "link_down"}:
            if target not in links:
                return SimulationEvent(event_id, event_type, target, "unknown_target", "link target is not present in topology")
            links[target]["state"] = "down"
            return SimulationEvent(event_id, event_type, target, "applied", "link logically disabled", (), (target,))
        if event_type in {"enable_link", "link_up"}:
            if target not in links:
                return SimulationEvent(event_id, event_type, target, "unknown_target", "link target is not present in topology")
            links[target]["state"] = "up"
            return SimulationEvent(event_id, event_type, target, "applied", "link logically enabled", (), (target,))
        return SimulationEvent(event_id, event_type, target, "unknown_event", "event type is not in the logical simulator vocabulary")

    @staticmethod
    def _evaluate_paths(nodes: Mapping[str, Mapping[str, Any]], links: Mapping[str, Mapping[str, Any]], intents: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
        """Evaluate declared expected reachability over active graph edges."""
        adjacency: dict[str, set[str]] = {name: set() for name in nodes}
        for link in links.values():
            if str(link.get("state", "")).lower() not in {"up", "active", "enabled"}:
                continue
            source = str(link.get("source"))
            target = str(link.get("target"))
            if source in nodes and target in nodes and NetworkSimulator._node_active(nodes[source]) and NetworkSimulator._node_active(nodes[target]):
                adjacency[source].add(target)
                adjacency[target].add(source)
        results: dict[str, str] = {}
        for path_id, intent in intents.items():
            source = str(intent.get("source", ""))
            destination = str(intent.get("destination", intent.get("target", "")))
            expected = str(intent.get("expected", "reachable")).lower()
            if source not in nodes or destination not in nodes or expected not in {"reachable", "unreachable"}:
                results[str(path_id)] = "not_verifiable_with_current_inputs"
                continue
            reachable = NetworkSimulator._reachable(source, destination, adjacency)
            correct = reachable if expected == "reachable" else not reachable
            results[str(path_id)] = "verified" if correct else "failed"
        return results

    @staticmethod
    def _node_active(node: Mapping[str, Any]) -> bool:
        """Treat only explicit active states as available in the logical graph."""
        return str(node.get("state", "")).lower() in {"up", "active", "enabled"}

    @staticmethod
    def _reachable(source: str, destination: str, adjacency: Mapping[str, set[str]]) -> bool:
        """Perform deterministic breadth-first logical reachability."""
        if source == destination:
            return True
        queue: deque[str] = deque([source])
        visited = {source}
        while queue:
            current = queue.popleft()
            for neighbor in sorted(adjacency.get(current, ())):
                if neighbor == destination:
                    return True
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    @staticmethod
    def _blocked(reason: str) -> SimulationResult:
        """Create an explicit simulator result with no production claim."""
        return SimulationResult("logical-simulation:blocked", SimulationStatus.BLOCKED_MISSING_HUMAN_DATA.value, NetworkSimulator.SIMULATOR_KIND, False, False, {}, {}, (), {}, (reason,), (), ("logical simulator requires explicit topology and intent inputs", "simulation evidence alone cannot authorize production change"))
