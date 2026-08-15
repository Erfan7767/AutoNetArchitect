"""Non-invasive connectivity observation evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from formal_verification.proof_status import ProofStatus


@dataclass(frozen=True)
class ConnectivityCheck:
    """One expected path compared with an explicit observation."""

    path_id: str
    status: str
    detail: str
    expected: dict[str, Any] = field(default_factory=dict)
    observed: dict[str, Any] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the path check."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class ConnectivityVerificationReport:
    """Aggregate connectivity verification outcome."""

    proof_status: str
    production_suitable: bool
    checks: tuple[ConnectivityCheck, ...]
    missing_inputs: tuple[str, ...] = ()
    evidence_basis: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the connectivity report."""
        return {
            "proof_status": self.proof_status,
            "production_suitable": self.production_suitable,
            "checks": [check.to_dict() for check in self.checks],
            "missing_inputs": list(self.missing_inputs),
            "evidence_basis": list(self.evidence_basis),
        }


class ConnectivityTester:
    """Evaluate supplied path tests without initiating network traffic."""

    def verify(self, expected_paths: Mapping[str, Mapping[str, Any]], observations: Mapping[str, Mapping[str, Any]] | None) -> ConnectivityVerificationReport:
        """Compare expected paths with explicit, externally collected observations."""
        if observations is None:
            return ConnectivityVerificationReport(ProofStatus.NOT_VERIFIABLE.value, False, (), ("connectivity_observations",))
        checks: list[ConnectivityCheck] = []
        evidence: set[str] = set()
        for path_id in sorted(expected_paths):
            expected = dict(expected_paths[path_id])
            observed = dict(observations.get(path_id, {}))
            if not observed:
                checks.append(ConnectivityCheck(path_id, ProofStatus.NOT_VERIFIABLE.value, "no observation supplied for expected path", expected=expected, observed={}))
                continue
            raw_status = str(observed.get("status", "")).lower()
            if raw_status in {"passed", "reachable", "up", "verified"}:
                status = ProofStatus.VERIFIED.value
                detail = "explicit observation reports reachable"
            elif raw_status in {"fail", "failed", "unreachable", "down"}:
                status = ProofStatus.FAILED.value
                detail = "explicit observation reports unreachable"
            else:
                status = ProofStatus.NOT_VERIFIABLE.value
                detail = "connectivity observation has no recognized status"
            if status == ProofStatus.VERIFIED.value:
                mismatches: list[str] = []
                if expected.get("max_latency_ms") is not None and observed.get("latency_ms") is not None and float(observed["latency_ms"]) > float(expected["max_latency_ms"]):
                    mismatches.append("latency_ms")
                if expected.get("max_packet_loss_pct") is not None and observed.get("packet_loss_pct") is not None and float(observed["packet_loss_pct"]) > float(expected["max_packet_loss_pct"]):
                    mismatches.append("packet_loss_pct")
                if mismatches:
                    status = ProofStatus.FAILED.value
                    detail = f"connectivity observation exceeds {', '.join(mismatches)}"
            ids = tuple(str(value) for value in observed.get("evidence_ids", ()) if value)
            evidence.update(ids)
            checks.append(ConnectivityCheck(path_id, status, detail, expected, observed, ids))
        statuses = {check.status for check in checks}
        proof = ProofStatus.FAILED.value if ProofStatus.FAILED.value in statuses else ProofStatus.NOT_VERIFIABLE.value if ProofStatus.NOT_VERIFIABLE.value in statuses else ProofStatus.VERIFIED.value
        return ConnectivityVerificationReport(proof, proof == ProofStatus.VERIFIED.value, tuple(checks), (), tuple(sorted(evidence)))
