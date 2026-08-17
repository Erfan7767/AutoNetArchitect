"""Operational tests proving laboratory validation remains distinct from production change control."""

from __future__ import annotations

from lab.lab_manager import LabAdapter, LabConfig, LabManager, LabOperation, LabState, LabTopology, LabVerificationExecution
from site_agent.validation_policy import ScenarioValidationPolicy
from site_agent.vendor_support import VendorFamily
from site_agent.virtual_adapters import LabValidationAdapter, VirtualValidationPath


class IsolatedLabAdapter:
    """A lab-only provider fixture that returns explicit non-production operation records."""

    provider_name = "isolated-lab"

    def deploy_topology(self, topology: LabTopology) -> LabOperation:
        """Return a successful lab deployment record with production controls still required."""

        return LabOperation(self.provider_name, "deploy_topology", LabState.EXECUTED.value, f"Lab topology {topology.topology_id} deployed.")

    def push_config(self, config: LabConfig) -> LabOperation:
        """Return a successful lab config record with no production authority."""

        return LabOperation(self.provider_name, "push_config", LabState.EXECUTED.value, f"Lab config for {config.device_id} applied.")

    def run_verification(self, plan: dict[str, object]) -> LabVerificationExecution:
        """Return lab observations for an explicit verification plan only."""

        return LabVerificationExecution(
            LabOperation(self.provider_name, "run_verification", LabState.EXECUTED.value, "Lab verification complete."),
            observations={"reachability": "passed", "routing": "passed"},
        )


def test_lab_operations_and_validation_plan_cannot_grant_production_change_authority() -> None:
    """Validate a complete isolated-lab sequence while preserving human production controls."""

    manager = LabManager([IsolatedLabAdapter()])
    topology = LabTopology(topology_id="lab-topology-001", nodes=({"id": "r1"}, {"id": "r2"}), links=({"a": "r1", "b": "r2"},))
    deployment = manager.deploy_topology("isolated-lab", topology)
    config = LabConfig(device_id="r1", vendor="Cisco", platform="IOS XE", rendered_config="hostname r1", artifact_hash="artifact-hash-001")
    config_result = manager.push_configs("isolated-lab", [config])[0]
    report = manager.run_verification("isolated-lab", {"checks": ["reachability", "routing"]}, {"reachability": "passed", "routing": "passed"})
    plan = LabValidationAdapter(VendorFamily.CISCO).plan("artifact-hash-001", "facts-hash-001", "scope-hash-001")
    policy = ScenarioValidationPolicy().evaluate(plan)

    assert deployment.validation_only and deployment.production_change_control_required
    assert config_result.validation_only and config_result.production_change_control_required
    assert report.validation_only and report.production_change_control_required
    assert report.comparison.status == "matched"
    assert plan.validation_path is VirtualValidationPath.LAB
    assert not plan.production_change_authority
    assert not policy.production_change_authority
