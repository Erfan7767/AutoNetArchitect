"""Non-invasive cable verification result evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from formal_verification.proof_status import ProofStatus


@dataclass(frozen=True)
class CableCheck:
    """One explicit cable or port verification result."""

    cable_id: str
    status: str
    detail: str
    expected: dict[str, Any] = field(default_factory=dict)
    observed: dict[str, Any] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize a cable check."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class CableVerificationReport:
    """Aggregate cable verification outcome."""

    proof_status: str
    production_suitable: bool
    checks: tuple[CableCheck, ...]
    missing_inputs: tuple[str, ...] = ()
    evidence_basis: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the cable report."""
        return {
            "proof_status": self.proof_status,
            "production_suitable": self.production_suitable,
            "checks": [check.to_dict() for check in self.checks],
            "missing_inputs": list(self.missing_inputs),
            "evidence_basis": list(self.evidence_basis),
        }


class CableTester:
    """Evaluate human or tool-supplied cable observations without active probing."""

    def evaluate(self, results: Mapping[str, Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None, expected: Mapping[str, Mapping[str, Any]] | None = None) -> CableVerificationReport:
        """Evaluate explicit results; no physical test is executed by this class."""
        if results is None:
            return CableVerificationReport(ProofStatus.NOT_VERIFIABLE.value, False, (), ("cable_test_results",))
        normalized = self._normalize(results)
        if not normalized:
            return CableVerificationReport(ProofStatus.NOT_VERIFIABLE.value, False, (), ("cable_test_results",))
        checks: list[CableCheck] = []
        evidence: set[str] = set()
        for cable_id in sorted(normalized):
            observed = normalized[cable_id]
            expected_item = dict((expected or {}).get(cable_id, {}))
            raw_status = str(observed.get("status", "")).lower()
            if raw_status in {"passed", "verified", "up"}:
                status = ProofStatus.VERIFIED.value
                detail = "explicit cable observation reports successful"
            elif raw_status in {"fail", "failed", "down"}:
                status = ProofStatus.FAILED.value
                detail = "explicit cable observation reports failure"
            else:
                status = ProofStatus.NOT_VERIFIABLE.value
                detail = "cable result does not contain a recognized status"
            mismatches = tuple(field for field in ("remote_port", "medium", "length_m") if expected_item.get(field) is not None and observed.get(field) is not None and expected_item[field] != observed[field])
            if mismatches and status == ProofStatus.VERIFIED.value:
                status = ProofStatus.FAILED.value
                detail = f"cable observation differs on {', '.join(mismatches)}"
            ids = tuple(str(value) for value in observed.get("evidence_ids", ()) if value)
            evidence.update(ids)
            checks.append(CableCheck(cable_id, status, detail, expected_item, observed, ids))
        statuses = {check.status for check in checks}
        proof = ProofStatus.FAILED.value if ProofStatus.FAILED.value in statuses else ProofStatus.NOT_VERIFIABLE.value if ProofStatus.NOT_VERIFIABLE.value in statuses else ProofStatus.VERIFIED.value
        return CableVerificationReport(proof, proof == ProofStatus.VERIFIED.value, tuple(checks), (), tuple(sorted(evidence)))

    @staticmethod
    def _normalize(results: Mapping[str, Mapping[str, Any]] | Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
        """Normalize mapping or iterable results by explicit cable identifier."""
        if isinstance(results, Mapping):
            return {str(key): dict(value) for key, value in results.items() if isinstance(value, Mapping)}
        normalized: dict[str, dict[str, Any]] = {}
        for item in results:
            if isinstance(item, Mapping) and item.get("cable_id"):
                normalized[str(item["cable_id"])] = dict(item)
        return normalized
