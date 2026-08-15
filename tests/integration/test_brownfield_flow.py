"""Integration tests for brownfield assisted migration boundaries."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from orchestrators import DeploymentOrchestrator, Preconditions, WorkflowStage
from tests.final_test_helpers import fixture_project, create_master


def test_brownfield_ambiguity_blocks_production_path():
    project = fixture_project("branch_brownfield")
    discovered = project["discovered_state"]["devices"]
    assert any(device["parse_confidence"] == "ambiguous" for device in discovered)
    assert project["migration"]["production_execution_allowed"] is False
    assert project["migration"]["requires_human_review"] is True


def test_brownfield_unresolved_inputs_are_preserved_as_blockers():
    with TemporaryDirectory() as tmp:
        master, _audit, _sot = create_master(Path(tmp))
        context = master.create_context(project_id="BranchBrownfield", actor="brownfield-engineer", unresolved_human_inputs=("existing_provider_handoff", "legacy_device_owner"))
        result = master.execute_stage(context, target_stage=WorkflowStage.REQUIREMENTS, preconditions=Preconditions(unresolved_human_inputs=("existing_provider_handoff",)), handler=lambda _context, _data: {"artifact_ids": ("REQ-B07",)}, input_data={})
        assert result.success is False
        assert result.status == "blocked"
        assert context.current_stage == WorkflowStage.QUESTIONNAIRE.value
        assert any("HumanSuppliedMandatory" in reason for reason in result.reasons)


def test_brownfield_deployment_prepare_cannot_skip_design_sot():
    with TemporaryDirectory() as tmp:
        master, _audit, _sot = create_master(Path(tmp))
        context = master.create_context(project_id="BranchBrownfield", actor="brownfield-engineer", completed_through=WorkflowStage.CONFIG_GENERATION)
        result = DeploymentOrchestrator(master=master).prepare(context, {"deployment_artifact_id": "B07-PREP"}, evidence_ids=("DISCOVERY-B07-001",))
        assert result.success is False
        assert any("SoT" in reason or "stage order" in reason for reason in result.reasons)
