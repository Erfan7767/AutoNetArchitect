"""Exact platform, version, license, and feature evidence assessment.

This module does not generate configuration or authorize execution.  It converts
observed facts plus referenced evidence into a bounded capability decision.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .models import ManagementProtocol, ObservedDeviceFacts
from .policy_catalog import PolicyDecision, VendorPolicyCatalog
from .vendor_support import CapabilityAssessment, SupportDecision, VendorCapabilityRegistry

DEFAULT_VENDOR_POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "vendor_support_policy.json"


class ExactCapabilityEvidence(BaseModel):
    """Secret-free identifiers and references necessary for a bounded assessment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    facts: ObservedDeviceFacts
    protocol: ManagementProtocol
    platform_family: str = Field(min_length=1, max_length=120)
    exact_model_evidence_reference: str | None = Field(default=None, min_length=1, max_length=200)
    license_evidence_reference: str | None = Field(default=None, min_length=1, max_length=200)
    configuration_path_evidence_reference: str | None = Field(default=None, min_length=1, max_length=200)
    requested_capabilities: tuple[str, ...] = ()


class ExactCapabilityAssessor:
    """Apply vendor identity, policy, and evidence checks without guessing missing facts."""

    def __init__(
        self,
        registry: VendorCapabilityRegistry | None = None,
        policy_catalog: VendorPolicyCatalog | None = None,
    ) -> None:
        """Use bounded contracts and reviewed policy data from controlled local sources."""

        self._registry = registry or VendorCapabilityRegistry()
        self._policy_catalog = policy_catalog or VendorPolicyCatalog(DEFAULT_VENDOR_POLICY_PATH)

    def assess(self, evidence: ExactCapabilityEvidence) -> CapabilityAssessment:
        """Return a conservative decision for exact observed identity and evidence references."""

        contract = self._registry.contract_for(evidence.facts)
        if contract is None:
            return CapabilityAssessment(
                decision=SupportDecision.UNSUPPORTED,
                reason="Observed vendor is not in the bounded four-family support registry.",
                required_evidence=("supported_vendor_family_evidence",),
            )
        if not contract.matches_platform(evidence.facts.platform):
            return self._review_required(
                contract.family,
                "Observed platform does not match the declared vendor contract; no platform inference is allowed.",
                contract.source_url,
                ("exact_platform_evidence",),
            )
        if evidence.protocol not in contract.protocols:
            return CapabilityAssessment(
                vendor_family=contract.family,
                decision=SupportDecision.UNSUPPORTED,
                reason="The selected management protocol is outside the vendor contract for this observed platform.",
                source_url=contract.source_url,
                required_evidence=("protocol_support_evidence",),
            )
        if not evidence.facts.software_version.strip() or not evidence.facts.serial_reference.strip():
            return self._review_required(
                contract.family,
                "Exact observed software version and device identity evidence are required.",
                contract.source_url,
                ("exact_software_version_evidence", "device_identity_evidence"),
            )
        if not evidence.exact_model_evidence_reference:
            return self._review_required(
                contract.family,
                "An exact observed model evidence reference is required; platform family alone is insufficient.",
                contract.source_url,
                ("exact_model_evidence",),
            )
        missing_capabilities = self._missing_requested_capabilities(evidence)
        if missing_capabilities:
            return self._review_required(
                contract.family,
                "Requested capabilities are not proven by observed device evidence.",
                contract.source_url,
                missing_capabilities,
            )
        policy_decision = self._policy_catalog.assess(
            vendor_family=contract.family.value,
            platform_family=evidence.platform_family,
            software_version=evidence.facts.software_version,
            license_evidence=bool(evidence.license_evidence_reference),
            configuration_path_evidence=bool(evidence.configuration_path_evidence_reference),
        )
        return self._to_capability_assessment(contract.family, contract.source_url, policy_decision)

    @staticmethod
    def _missing_requested_capabilities(evidence: ExactCapabilityEvidence) -> tuple[str, ...]:
        """Return sorted capabilities absent from the observed evidence without deriving new facts."""

        observed = set(evidence.facts.capabilities)
        requested = set(_non_empty_values(evidence.requested_capabilities))
        return tuple(sorted(requested - observed))

    @staticmethod
    def _review_required(
        family: object,
        reason: str,
        source_url: str,
        required_evidence: tuple[str, ...],
    ) -> CapabilityAssessment:
        """Construct a consistent non-authorizing review result for a known vendor family."""

        return CapabilityAssessment(
            vendor_family=family,  # type: ignore[arg-type]
            decision=SupportDecision.REVIEW_REQUIRED,
            reason=reason,
            source_url=source_url,
            required_evidence=required_evidence,
        )

    @staticmethod
    def _to_capability_assessment(
        family: object,
        source_url: str,
        policy: PolicyDecision,
    ) -> CapabilityAssessment:
        """Map the reviewed policy result to the capability API without adding authority."""

        decision = {
            "configuration_supported": SupportDecision.CONFIGURATION_SUPPORTED,
            "review_required": SupportDecision.REVIEW_REQUIRED,
            "blocked": SupportDecision.UNSUPPORTED,
            "unsupported": SupportDecision.UNSUPPORTED,
        }.get(policy.decision, SupportDecision.REVIEW_REQUIRED)
        return CapabilityAssessment(
            vendor_family=family,  # type: ignore[arg-type]
            decision=decision,
            reason=policy.reason,
            source_url=policy.source_urls[0] if policy.source_urls else source_url,
            production_configuration_allowed=False,
            required_evidence=policy.required_evidence,
        )


def _non_empty_values(values: Iterable[str]) -> tuple[str, ...]:
    """Normalize supplied capability labels while retaining no implicit default values."""

    return tuple(value.strip() for value in values if value.strip())
