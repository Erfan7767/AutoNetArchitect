"""Tests for the Windows-local evidence-bound virtual validation workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from site_agent.discovery_coordination import DiscoveryBatchResult
from site_agent.evidence_handoff import DesignEvidenceHandoff
from site_agent.lab_authorization import LaboratoryAuthorization, LaboratoryEnvironmentClass
from site_agent.models import (
    DiscoveryResult,
    DiscoveryState,
    DiscoveryTarget,
    ManagementProtocol,
    ObservedDeviceFacts,
    VirtualTestResult,
    VirtualTestState,
)
from site_agent.scope import AuthorizedScope
from site_agent.vendor_support import CapabilityAssessment, SupportDecision, VendorFamily
from site_agent.virtual_adapters import LabValidationAdapter
from windows_app.validation_review import LocalValidationReviewDraft, WindowsValidationReviewController
from windows_app.virtual_validation import LocalVirtualValidationController
from windows_app.workspace import WindowsWorkspace


def approved_scope() -> AuthorizedScope:
    """Return an explicit human-approved local scope for the virtual-validation tests."""

    return AuthorizedScope(
        site_id="site-hq",
        approved_networks=("10.0.0.0/24",),
        approved_targets=("10.0.0.10",),
        allowed_protocols=("ssh",),
        approval_reference="customer-approval-01",
        operator_acknowledged=True,
    )


def approved_laboratory_authorization(scope: AuthorizedScope) -> LaboratoryAuthorization:
    """Return an active written authorization for a non-production lab bound to the supplied scope."""

    return LaboratoryAuthorization(
        authorization_reference="written-lab-authorization-001",
        human_authorizer="Named lab approver",
        scope_hash=scope.evidence_hash(),
        environment_reference="isolated-vendor-image-lab-001",
        environment_class=LaboratoryEnvironmentClass.VENDOR_IMAGE_LAB,
        approved_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )


def handoff(scope_hash: str) -> DesignEvidenceHandoff:
    """Return a resolved exact-evidence handoff tied to the supplied scope hash."""

    return DesignEvidenceHandoff(
        site_id="site-hq",
        scope_hash=scope_hash,
        requirements_hash="requirements-hash",
        design_artifact_hash="artifact-hash",
        target_facts_hash="facts-hash",
        discovery_evidence_reference="discovery-run-01",
        capability_assessment_reference="capability-review-01",
        capability_assessment=CapabilityAssessment(
            vendor_family=VendorFamily.CISCO,
            decision=SupportDecision.CONFIGURATION_SUPPORTED,
            reason="Exact platform, version, license, feature, and path evidence were reviewed.",
        ),
    )


def test_windows_local_virtual_validation_persists_only_redacted_hash_bound_evidence(tmp_path: Path) -> None:
    """A completed local test stays evidence-only and preserves exact hash binding."""

    workspace = WindowsWorkspace(tmp_path)
    scope = approved_scope()
    workspace.save_scope(scope)
    workspace.save_laboratory_authorization(approved_laboratory_authorization(scope))
    batch = DiscoveryBatchResult(site_id="site-hq", scope_hash=scope.evidence_hash(), results=())

    def result_adapter(artifact_hash: str, target_facts_hash: str, scope_hash: str) -> VirtualTestResult:
        return VirtualTestResult(
            state=VirtualTestState.TEST_PASSED,
            adapter_kind="lab-validation",
            fidelity_label="vendor_image_lab",
            artifact_hash=artifact_hash,
            target_facts_hash=target_facts_hash,
            scope_hash=scope_hash,
            detail="Lab evidence matched. token=do-not-store",
        )

    record = LocalVirtualValidationController(workspace, result_adapter).validate(
        batch,
        handoff(scope.evidence_hash()),
        LabValidationAdapter(VendorFamily.CISCO),
    )

    assert record.production_execution_permitted is False
    assert record.result.state is VirtualTestState.TEST_PASSED
    assert record.result.scope_hash == scope.evidence_hash()
    persisted = workspace.load_virtual_test_result()
    assert persisted is not None
    assert "do-not-store" not in persisted.detail


def test_windows_local_virtual_validation_rejects_cross_scope_handoff(tmp_path: Path) -> None:
    """A local scope must exactly match the handoff before an adapter can run."""

    workspace = WindowsWorkspace(tmp_path)
    scope = approved_scope()
    workspace.save_scope(scope)
    workspace.save_laboratory_authorization(approved_laboratory_authorization(scope))
    batch = DiscoveryBatchResult(site_id="site-hq", scope_hash="other-scope-hash", results=())

    controller = LocalVirtualValidationController(workspace, lambda artifact_hash, target_facts_hash, scope_hash: VirtualTestResult(
        state=VirtualTestState.TEST_PASSED,
        adapter_kind="lab-validation",
        fidelity_label="vendor_image_lab",
        artifact_hash=artifact_hash,
        target_facts_hash=target_facts_hash,
        scope_hash=scope_hash,
        detail="unused",
    ))

    with pytest.raises(ValueError, match="scope hash"):
        controller.validate(batch, handoff("other-scope-hash"), LabValidationAdapter(VendorFamily.CISCO))


def test_windows_local_virtual_validation_rejects_adapter_or_fidelity_mismatch(tmp_path: Path) -> None:
    """A matching hash record still fails when it claims the wrong local test path or fidelity."""

    workspace = WindowsWorkspace(tmp_path)
    scope = approved_scope()
    workspace.save_scope(scope)
    workspace.save_laboratory_authorization(approved_laboratory_authorization(scope))
    batch = DiscoveryBatchResult(site_id="site-hq", scope_hash=scope.evidence_hash(), results=())
    controller = LocalVirtualValidationController(workspace, lambda artifact_hash, target_facts_hash, scope_hash: VirtualTestResult(
        state=VirtualTestState.TEST_PASSED,
        adapter_kind="different-adapter",
        fidelity_label="logical_intent_only",
        artifact_hash=artifact_hash,
        target_facts_hash=target_facts_hash,
        scope_hash=scope_hash,
        detail="Mismatched evidence record.",
    ))

    with pytest.raises(ValueError, match="adapter or fidelity"):
        controller.validate(batch, handoff(scope.evidence_hash()), LabValidationAdapter(VendorFamily.CISCO))


class SupportedCapabilityAssessor:
    """Provide a reviewed exact capability outcome for Windows review-controller tests."""

    def assess(self, _evidence: object) -> CapabilityAssessment:
        """Return a non-authorizing supported decision with no execution grant."""

        return CapabilityAssessment(
            vendor_family=VendorFamily.CISCO,
            decision=SupportDecision.CONFIGURATION_SUPPORTED,
            reason="Exact reviewed evidence supports a lab-validation plan only.",
        )


def observed_discovery_result() -> DiscoveryResult:
    """Return one scope-authorized discovery result with explicit observed facts."""

    return DiscoveryResult(
        target=DiscoveryTarget(address="10.0.0.10", protocol=ManagementProtocol.SSH, credential_reference="secret://device-reference"),
        state=DiscoveryState.DISCOVERED,
        facts=ObservedDeviceFacts(vendor="Cisco", platform="IOS XE", software_version="17.13.1", serial_reference="observed-serial", interface_count=24),
        message="Observed facts were recorded through the approved read-only scope.",
    )


def validation_draft() -> LocalValidationReviewDraft:
    """Return non-secret human evidence references for a local validation-plan review."""

    return LocalValidationReviewDraft(
        artifact_hash="generated-artifact-hash",
        platform_family="network_os",
        exact_model_evidence_reference="observed-model-evidence",
        license_evidence_reference="license-evidence",
        configuration_path_evidence_reference="configuration-path-evidence",
    )


def test_windows_validation_review_prepares_a_plan_from_selected_observed_facts(tmp_path: Path) -> None:
    """The Windows review flow binds the selected fact record, scope, and artifact hash before queuing lab validation."""

    workspace = WindowsWorkspace(tmp_path)
    scope = approved_scope()
    workspace.save_scope(scope)
    workspace.save_laboratory_authorization(approved_laboratory_authorization(scope))

    plan = WindowsValidationReviewController(workspace, SupportedCapabilityAssessor()).prepare_plan(observed_discovery_result(), validation_draft())

    assert plan.artifact_hash == "generated-artifact-hash"
    assert plan.scope_hash == scope.evidence_hash()
    assert plan.production_change_authority is False
    assert plan.adapter_kind == "lab-validation"


def test_windows_validation_review_rejects_unresolved_discovery_result(tmp_path: Path) -> None:
    """The Windows review flow abstains when the selected device does not have observed facts."""

    workspace = WindowsWorkspace(tmp_path)
    workspace.save_scope(approved_scope())
    unresolved = DiscoveryResult(
        target=DiscoveryTarget(address="10.0.0.10", protocol=ManagementProtocol.SSH, credential_reference="secret://device-reference"),
        state=DiscoveryState.AMBIGUOUS,
        message="Observed identity is ambiguous.",
    )

    with pytest.raises(ValueError, match="observed device facts"):
        WindowsValidationReviewController(workspace, SupportedCapabilityAssessor()).prepare_plan(unresolved, validation_draft())


def test_windows_virtual_validation_rejects_missing_or_scope_mismatched_written_lab_authorization(tmp_path: Path) -> None:
    """No local lab plan is prepared unless a current written authorization matches the exact approved scope hash."""

    workspace = WindowsWorkspace(tmp_path)
    scope = approved_scope()
    workspace.save_scope(scope)
    batch = DiscoveryBatchResult(site_id="site-hq", scope_hash=scope.evidence_hash(), results=())

    with pytest.raises(PermissionError, match="written human laboratory authorization"):
        LocalVirtualValidationController(workspace).prepare(batch, handoff(scope.evidence_hash()), LabValidationAdapter(VendorFamily.CISCO))

    workspace.save_laboratory_authorization(approved_laboratory_authorization(scope).model_copy(update={"scope_hash": "different-approved-scope"}))
    with pytest.raises(PermissionError, match="outside the approved scope"):
        LocalVirtualValidationController(workspace).prepare(batch, handoff(scope.evidence_hash()), LabValidationAdapter(VendorFamily.CISCO))
