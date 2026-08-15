"""Auditable Digital Twin reporting with explicit fidelity and state provenance."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

from .drift_timeline import DriftEvent
from .temporal_state_store import TemporalSnapshot
from .traffic_intent_overlay import TrafficOverlayResult
from .twin_confidence import TwinConfidenceReport
from .twin_model import StateCertainty, TwinModel


@dataclass(frozen=True)
class TwinReport:
    """Integrated Digital Twin report for engineering review."""

    twin_id: str
    state_views: dict[str, int]
    state_distinctions: tuple[str, ...]
    confidence: TwinConfidenceReport
    drift_events: tuple[DriftEvent, ...] = ()
    traffic_overlay: tuple[TrafficOverlayResult, ...] = ()
    replay_snapshot_ids: tuple[str, ...] = ()
    verified_claims: tuple[str, ...] = ()
    unverified_claims: tuple[str, ...] = ()
    fidelity_cap: str = "evidence_bounded"
    production_gate: str = "block_or_review"
    production_safe_claim_allowed: bool = False
    limitations: tuple[str, ...] = ("logical and observed views are not protocol emulation", "inferred transient states remain explicitly uncertain", "report does not authorize production change")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report with all uncertainty fields retained."""
        return {
            "twin_id": self.twin_id,
            "state_views": dict(self.state_views),
            "state_distinctions": list(self.state_distinctions),
            "confidence": self.confidence.to_dict(),
            "drift_events": [event.to_dict() for event in self.drift_events],
            "traffic_overlay": [item.to_dict() for item in self.traffic_overlay],
            "replay_snapshot_ids": list(self.replay_snapshot_ids),
            "verified_claims": list(self.verified_claims),
            "unverified_claims": list(self.unverified_claims),
            "fidelity_cap": self.fidelity_cap,
            "production_gate": self.production_gate,
            "production_safe_claim_allowed": self.production_safe_claim_allowed,
            "limitations": list(self.limitations),
        }


class TwinReporter:
    """Build a review report from twin state and attached evidence."""

    def report(
        self,
        twin: TwinModel,
        confidence: TwinConfidenceReport,
        *,
        drift_events: Sequence[DriftEvent] = (),
        traffic_overlay: Sequence[TrafficOverlayResult] = (),
        replay_snapshots: Sequence[TemporalSnapshot] = (),
    ) -> TwinReport:
        """Aggregate views without collapsing observed and inferred state."""
        state_views: dict[str, int] = {}
        for state in twin.states:
            state_views[state.kind] = state_views.get(state.kind, 0) + 1
        distinctions = (
            "logical_model is declared design intent",
            "deployment_state is declared deployment evidence",
            "discovered_operational_state is observed discovery evidence",
            "operational_state is observed runtime evidence",
            "inferred_transient_state is an explicitly inferred projection",
            "replayed_historical_state is reconstructed from timestamped events",
        )
        verified: list[str] = []
        unverified: list[str] = []
        if state_views.get("discovered_operational_state", 0):
            verified.append("discovered operational state exists in the supplied evidence set")
        else:
            unverified.append("no discovered operational state is present")
        if state_views.get("operational_state", 0):
            verified.append("operational state observations exist in the supplied evidence set")
        else:
            unverified.append("no operational state observation is present")
        if state_views.get("inferred_transient_state", 0):
            unverified.append("inferred transient state exists and must not be treated as observed fact")
        if state_views.get("replayed_historical_state", 0):
            verified.append("historical state can be traced to replayed event evidence")
        else:
            unverified.append("no replayed historical state is present")
        if confidence.full_fidelity_claim:
            verified.append("full fidelity claim is backed by the explicitly supplied fidelity evidence")
        else:
            unverified.append("full protocol fidelity is not established")
        if confidence.missing_state_kinds:
            unverified.append("required state views are missing: " + ", ".join(confidence.missing_state_kinds))
        if drift_events:
            unverified.append(f"{len(drift_events)} drift events require engineering review")
        return TwinReport(twin.twin_id, dict(sorted(state_views.items())), distinctions, confidence, tuple(drift_events), tuple(traffic_overlay), tuple(snapshot.snapshot_id for snapshot in replay_snapshots), tuple(dict.fromkeys(verified)), tuple(dict.fromkeys(unverified)), confidence.fidelity_cap, "block_or_review", False)
