"""Analysis-only failure injection for Digital Twin scenarios."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Sequence

from .state_ingestor import StateIngestor
from .twin_model import StateCertainty, StateProvenance, TwinModel, TwinState, TwinStateKind


@dataclass(frozen=True)
class FailureInjectionRequest:
    """Explicit bounded failure scenario request."""

    injection_id: str
    entity_id: str
    failure_type: str
    rationale: str
    analysis_only: bool = True
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the request."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class FailureInjectionResult:
    """Projected state result from an analysis-only failure scenario."""

    injection_id: str
    status: str
    original_twin_id: str
    projected_twin: TwinModel | None
    injected_state: TwinState | None
    production_execution_allowed: bool = False
    safety_policies_preserved: tuple[str, ...] = ("management_access", "audit_logging", "rollback_control")
    limitations: tuple[str, ...] = ("projection only", "does not execute a device action", "does not prove physical or protocol behavior")
    required_human_inputs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result without hiding analysis limitations."""
        return {"injection_id": self.injection_id, "status": self.status, "original_twin_id": self.original_twin_id, "projected_twin": self.projected_twin.to_dict() if self.projected_twin else None, "injected_state": self.injected_state.to_dict() if self.injected_state else None, "production_execution_allowed": self.production_execution_allowed, "safety_policies_preserved": list(self.safety_policies_preserved), "limitations": list(self.limitations), "required_human_inputs": list(self.required_human_inputs)}


class FailureInjector:
    """Create isolated logical failure projections from a TwinModel."""

    def inject(self, twin: TwinModel, request: FailureInjectionRequest) -> FailureInjectionResult:
        """Return a projected twin and never mutate or execute against the source."""
        if not request.analysis_only:
            return FailureInjectionResult(request.injection_id, "blocked_unsafe_mode", twin.twin_id, None, None, False, required_human_inputs=("analysis_only=True",))
        if not request.entity_id or not request.failure_type:
            return FailureInjectionResult(request.injection_id, "blocked_missing_human_data", twin.twin_id, None, None, False, required_human_inputs=("entity_id", "failure_type"))
        base = twin.latest(request.entity_id)
        if base is None:
            return FailureInjectionResult(request.injection_id, "unknown_entity", twin.twin_id, None, None, False, required_human_inputs=(f"twin_state:{request.entity_id}",))
        timestamp = datetime.now(timezone.utc).isoformat()
        values = dict(base.values) | {"failure_type": request.failure_type, "state": "failed", "injected": True}
        provenance = StateProvenance("failure_injection", request.evidence_ids, timestamp, timestamp, timestamp, None, StateCertainty.INFERRED.value, 0.25)
        state_id = f"injected:{request.injection_id}:{request.entity_id}"
        state_hash = StateIngestor._hash({"state_id": state_id, "entity_id": request.entity_id, "kind": TwinStateKind.INFERRED_TRANSIENT.value, "values": values, "provenance": provenance.to_dict()})
        injected = TwinState(state_id, request.entity_id, TwinStateKind.INFERRED_TRANSIENT.value, values, provenance, base.version + 1, state_hash)
        projected = twin.add_state(injected)
        return FailureInjectionResult(request.injection_id, "projected", twin.twin_id, projected, injected)

    def inject_many(self, twin: TwinModel, requests: Sequence[FailureInjectionRequest]) -> tuple[FailureInjectionResult, ...]:
        """Create independent sequential projections while preserving analysis-only boundaries."""
        current = twin
        results: list[FailureInjectionResult] = []
        for request in requests:
            result = self.inject(current, request)
            results.append(result)
            if result.projected_twin is not None:
                current = result.projected_twin
        return tuple(results)
