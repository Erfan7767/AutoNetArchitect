"""Reusable helpers for the comprehensive final test layer."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from audit.audit_trail import AuditTrail
from auth.rbac import Principal
from orchestrators import MasterOrchestrator, WorkflowContext, WorkflowStage
from persistence.project_persistence import ProjectPersistence
from source_of_truth.sot_manager import SoTManager

from .conftest import load_json_fixture


SUPPORTED_VENDORS = ("aruba", "cisco", "fortinet", "huawei", "juniper", "mikrotik", "paloalto")


def fixture_project(name: str) -> dict[str, Any]:
    """Load one golden project by fixture stem."""
    return load_json_fixture(f"golden_projects/{name}.json")


def seed_project(store: ProjectPersistence, fixture: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    """Persist one golden project and return payload plus checksum."""
    project_id = str(fixture["project_id"])
    result = store.save(project_id, dict(fixture))
    return dict(fixture), result.checksum


def create_master(root: Path) -> tuple[MasterOrchestrator, AuditTrail, SoTManager]:
    """Create isolated master orchestration dependencies."""
    audit = AuditTrail(root / "audit.jsonl")
    sot = SoTManager(root / "sot.json")
    return MasterOrchestrator(sot_manager=sot, audit_trail=audit), audit, sot


def context_at(master: MasterOrchestrator, project_id: str, stage: WorkflowStage, *, actor: str = "test-engineer", evidence: tuple[str, ...] = (), approvals: tuple[str, ...] = ()) -> WorkflowContext:
    """Create a deterministic contiguous workflow context."""
    return master.create_context(project_id=project_id, actor=actor, completed_through=stage, evidence_ids=evidence, approval_references=approvals, supervised_mode=True)


def admin_principal() -> Principal:
    """Return an explicit admin principal for direct service-boundary tests."""
    return Principal("test-admin", ("admin",), "test-session")


def assert_supported_vendor_set(vendors: list[str]) -> None:
    """Validate that a fixture only uses official V1 vendor families."""
    unknown = sorted(set(vendors) - set(SUPPORTED_VENDORS))
    if unknown:
        raise AssertionError(f"fixture contains unsupported vendors: {unknown}")
