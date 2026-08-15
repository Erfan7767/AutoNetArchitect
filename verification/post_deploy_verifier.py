"""Post-deployment verification baselines with explicit proof status."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from formal_verification.proof_status import ProofStatus

from discovery.discovery_models import DeviceProfile


@dataclass(frozen=True)
class VerificationCheck:
    """One independently traceable post-deployment check."""

    check_id: str
    category: str
    status: str
    detail: str
    expected: dict[str, Any] = field(default_factory=dict)
    observed: dict[str, Any] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the check and its uncertainty."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids), "assumptions": list(self.assumptions)}


@dataclass(frozen=True)
class PostDeployVerificationReport:
    """Verification report consumable by a deployment gate."""

    proof_status: str
    production_suitable: bool
    deployment_gate: str
    checks: tuple[VerificationCheck, ...]
    verified_claims: tuple[str, ...]
    unverified_claims: tuple[str, ...]
    assumptions_affecting_proof: tuple[str, ...]
    evidence_basis: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report without converting unknowns into passes."""
        return {
            "proof_status": self.proof_status,
            "production_suitable": self.production_suitable,
            "deployment_gate": self.deployment_gate,
            "checks": [check.to_dict() for check in self.checks],
            "verified_claims": list(self.verified_claims),
            "unverified_claims": list(self.unverified_claims),
            "assumptions_affecting_proof": list(self.assumptions_affecting_proof),
            "evidence_basis": list(self.evidence_basis),
        }


class PostDeployVerifier:
    """Verify identity and runtime observations supplied after deployment.

    The V1 verifier is observation-driven. It does not log in, change configuration,
    run intrusive probes, or claim production readiness when evidence is absent.
    """

    IDENTITY_FIELDS = ("vendor", "platform", "model", "version", "serial", "hostname")

    def verify(
        self,
        expected_devices: Mapping[str, Mapping[str, Any]],
        discovered_devices: Mapping[str, DeviceProfile | Mapping[str, Any]],
        operational_observations: Mapping[str, Mapping[str, Any]] | None = None,
        cable_results: Mapping[str, Mapping[str, Any]] | None = None,
        connectivity_results: Mapping[str, Mapping[str, Any]] | None = None,
        evidence_ids: tuple[str, ...] = (),
    ) -> PostDeployVerificationReport:
        """Evaluate supplied post-deployment evidence for each expected device."""
        checks: list[VerificationCheck] = []
        assumptions: set[str] = set()
        evidence: set[str] = set(evidence_ids)
        for device_id in sorted(expected_devices):
            expected = dict(expected_devices[device_id])
            discovered = discovered_devices.get(device_id)
            if discovered is None:
                checks.append(VerificationCheck(f"identity:{device_id}", "identity", ProofStatus.NOT_VERIFIABLE.value, "no discovered device profile was supplied", expected=expected, assumptions=(f"discovered profile required for {device_id}",)))
                assumptions.add(f"discovered profile required for {device_id}")
                continue
            observed = self._as_dict(discovered)
            evidence.update(value for value in (observed.get("evidence_hash"),) if value)
            if observed.get("status") in {"unsupported_vendor", "unsupported", "unknown_device", "ambiguous"} or observed.get("confidence") in {"unknown", "ambiguous"}:
                checks.append(VerificationCheck(f"identity:{device_id}", "identity", ProofStatus.NOT_VERIFIABLE.value, "discovered identity is unsupported or ambiguous", expected=expected, observed=observed, assumptions=(f"authoritative identity required for {device_id}",)))
                assumptions.add(f"authoritative identity required for {device_id}")
                continue
            differences = tuple(field for field in self.IDENTITY_FIELDS if expected.get(field) and observed.get(field) and str(expected[field]) != str(observed[field]))
            if differences:
                checks.append(VerificationCheck(f"identity:{device_id}", "identity", ProofStatus.FAILED.value, f"identity differs on {', '.join(differences)}", expected=expected, observed=observed, evidence_ids=tuple(value for value in (observed.get("evidence_hash"),) if value)))
            else:
                checks.append(VerificationCheck(f"identity:{device_id}", "identity", ProofStatus.VERIFIED.value, "supplied identity fields match", expected=expected, observed=observed, evidence_ids=tuple(value for value in (observed.get("evidence_hash"),) if value)))
            operational = (operational_observations or {}).get(device_id)
            if operational is None:
                checks.append(VerificationCheck(f"operational:{device_id}", "operational", ProofStatus.NOT_VERIFIABLE.value, "no operational observation was supplied", assumptions=(f"runtime health observation required for {device_id}",)))
                assumptions.add(f"runtime health observation required for {device_id}")
            else:
                checks.append(self._operational_check(device_id, operational))
                evidence.update(str(value) for value in operational.get("evidence_ids", ()) if value)
            self._optional_result_check(checks, cable_results, device_id, "cable", "cable test")
            self._optional_result_check(checks, connectivity_results, device_id, "connectivity", "connectivity test")
        return self._build_report(checks, assumptions, evidence)

    @staticmethod
    def _as_dict(value: DeviceProfile | Mapping[str, Any]) -> dict[str, Any]:
        """Convert a profile or mapping into a comparable dictionary."""
        return value.to_dict() if isinstance(value, DeviceProfile) else dict(value)

    @staticmethod
    def _operational_check(device_id: str, observation: Mapping[str, Any]) -> VerificationCheck:
        """Evaluate a non-secret boolean runtime observation."""
        healthy = observation.get("healthy")
        if healthy is True:
            status = ProofStatus.VERIFIED.value
            detail = "explicit runtime observation reports healthy"
        elif healthy is False:
            status = ProofStatus.FAILED.value
            detail = "explicit runtime observation reports unhealthy"
        else:
            status = ProofStatus.NOT_VERIFIABLE.value
            detail = "runtime observation lacks a boolean healthy value"
        return VerificationCheck(f"operational:{device_id}", "operational", status, detail, observed=dict(observation), evidence_ids=tuple(str(value) for value in observation.get("evidence_ids", ()) if value))

    @staticmethod
    def _optional_result_check(checks: list[VerificationCheck], result_map: Mapping[str, Mapping[str, Any]] | None, device_id: str, category: str, label: str) -> None:
        """Include optional cable/connectivity evidence only when explicitly supplied."""
        if result_map is None or device_id not in result_map:
            return
        result = dict(result_map[device_id])
        status = str(result.get("status", ""))
        if status in {"verified", "passed", ProofStatus.VERIFIED.value}:
            proof = ProofStatus.VERIFIED.value
        elif status in {"failed", "fail", "failed_test", ProofStatus.FAILED.value}:
            proof = ProofStatus.FAILED.value
        else:
            proof = ProofStatus.NOT_VERIFIABLE.value
        checks.append(VerificationCheck(f"{category}:{device_id}", category, proof, f"{label} result evaluated from supplied evidence", observed=result, evidence_ids=tuple(str(value) for value in result.get("evidence_ids", ()) if value)))

    @staticmethod
    def _build_report(checks: list[VerificationCheck], assumptions: set[str], evidence: set[str]) -> PostDeployVerificationReport:
        """Compute proof status and gate from check outcomes."""
        statuses = {check.status for check in checks}
        if not checks or ProofStatus.NOT_VERIFIABLE.value in statuses:
            proof_status = ProofStatus.NOT_VERIFIABLE.value if not ProofStatus.FAILED.value in statuses else ProofStatus.FAILED.value
        elif ProofStatus.FAILED.value in statuses:
            proof_status = ProofStatus.FAILED.value
        elif statuses == {ProofStatus.VERIFIED.value}:
            proof_status = ProofStatus.VERIFIED.value
        else:
            proof_status = ProofStatus.PARTIALLY_VERIFIED.value
        verified = tuple(check.check_id for check in checks if check.status == ProofStatus.VERIFIED.value)
        unverified = tuple(check.check_id for check in checks if check.status != ProofStatus.VERIFIED.value)
        return PostDeployVerificationReport(proof_status, proof_status == ProofStatus.VERIFIED.value, "allow" if proof_status == ProofStatus.VERIFIED.value else "block_or_review", tuple(checks), verified, unverified, tuple(sorted(assumptions)), tuple(sorted(evidence)))
