"""GNS3 lab adapter for validation-only workflows."""

from __future__ import annotations

from typing import Any, Mapping

from .adapter_common import BaseLabAdapter
from .lab_manager import LabConfig, LabOperation, LabState, LabTopology, LabVerificationExecution


class Gns3Adapter(BaseLabAdapter):
    """Adapt provider-neutral lab intents to GNS3 project-shaped payloads."""

    def __init__(self, executor=None) -> None:
        """Create a GNS3 adapter with an optional explicit driver."""
        super().__init__("gns3", executor)

    def deploy_topology(self, topology: LabTopology) -> LabOperation:
        """Deploy a project topology to a GNS3 validation environment."""
        if not topology.topology_id or not topology.nodes:
            return LabOperation(self.provider_name, "deploy_topology", LabState.BLOCKED_MISSING_HUMAN_DATA.value, "GNS3 topology requires topology_id and nodes", True, True, required_human_inputs=("topology_id", "nodes"))
        payload = {
            "project_name": topology.topology_id,
            "nodes": [self._gns3_node(node) for node in topology.nodes],
            "links": [dict(link) for link in topology.links],
            "variables": dict(topology.variables),
            "design_ids": list(topology.design_ids),
            "source_of_truth_ids": list(topology.source_of_truth_ids),
        }
        return self._operation("deploy_topology", payload)

    def push_config(self, config: LabConfig) -> LabOperation:
        """Push a rendered startup configuration into a GNS3 node."""
        if not config.device_id or not config.rendered_config:
            return LabOperation(self.provider_name, "push_config", LabState.BLOCKED_MISSING_HUMAN_DATA.value, "GNS3 config push requires device_id and rendered_config", True, True, required_human_inputs=("device_id", "rendered_config"))
        payload = {"node_name": config.device_id, "vendor": config.vendor, "platform": config.platform, "startup_config": config.rendered_config, "artifact_id": config.artifact_id, "artifact_hash": config.artifact_hash, "decision_ids": list(config.decision_ids), "secret_references": list(config.secret_references)}
        return self._operation("push_config", payload)

    def run_verification(self, plan: Mapping[str, Any]) -> LabVerificationExecution:
        """Run a read-only GNS3 verification plan through the optional driver."""
        payload = {"project_name": str(plan.get("topology_id", plan.get("project_name", ""))), "checks": list(plan.get("checks", ())), "commands": dict(plan.get("commands", {})), "read_only": True}
        return self._verification(plan, payload)

    @staticmethod
    def _gns3_node(node: Mapping[str, Any]) -> dict[str, Any]:
        """Map a generic node to GNS3 template metadata."""
        return {"name": str(node.get("name", "")), "template": str(node.get("template", node.get("platform", ""))), "node_type": str(node.get("node_type", "")), "compute_id": str(node.get("compute_id", "")), "console_type": str(node.get("console_type", "telnet"))}
