"""EVE-NG lab adapter for validation-only topology and configuration workflows."""

from __future__ import annotations

from typing import Any, Mapping

from .adapter_common import BaseLabAdapter
from .lab_manager import LabConfig, LabOperation, LabState, LabTopology, LabVerificationExecution


class EveNgAdapter(BaseLabAdapter):
    """Adapt provider-neutral lab intents to EVE-NG-shaped payloads."""

    def __init__(self, executor=None) -> None:
        """Create an EVE-NG adapter with an optional explicitly supplied driver."""
        super().__init__("eve-ng", executor)

    def deploy_topology(self, topology: LabTopology) -> LabOperation:
        """Deploy a topology definition to an EVE-NG validation lab."""
        if not topology.topology_id or not topology.nodes:
            return LabOperation(self.provider_name, "deploy_topology", LabState.BLOCKED_MISSING_HUMAN_DATA.value, "EVE-NG topology requires topology_id and nodes", True, True, required_human_inputs=("topology_id", "nodes"))
        payload = {
            "lab_name": topology.topology_id,
            "nodes": [self._eve_node(node) for node in topology.nodes],
            "links": [dict(link) for link in topology.links],
            "variables": dict(topology.variables),
            "design_ids": list(topology.design_ids),
            "source_of_truth_ids": list(topology.source_of_truth_ids),
        }
        return self._operation("deploy_topology", payload)

    def push_config(self, config: LabConfig) -> LabOperation:
        """Push one rendered configuration into an EVE-NG node."""
        if not config.device_id or not config.rendered_config:
            return LabOperation(self.provider_name, "push_config", LabState.BLOCKED_MISSING_HUMAN_DATA.value, "EVE-NG config push requires device_id and rendered_config", True, True, required_human_inputs=("device_id", "rendered_config"))
        payload = {"node_name": config.device_id, "vendor": config.vendor, "platform": config.platform, "startup_config": config.rendered_config, "artifact_id": config.artifact_id, "artifact_hash": config.artifact_hash, "decision_ids": list(config.decision_ids), "secret_references": list(config.secret_references)}
        return self._operation("push_config", payload)

    def run_verification(self, plan: Mapping[str, Any]) -> LabVerificationExecution:
        """Run an EVE-NG verification plan through the optional provider driver."""
        payload = {"lab_name": str(plan.get("topology_id", plan.get("lab_name", ""))), "checks": list(plan.get("checks", ())), "commands": dict(plan.get("commands", {})), "read_only": True}
        return self._verification(plan, payload)

    @staticmethod
    def _eve_node(node: Mapping[str, Any]) -> dict[str, Any]:
        """Map a generic lab node to EVE-NG node metadata."""
        return {"name": str(node.get("name", "")), "template": str(node.get("template", node.get("platform", ""))), "image": str(node.get("image", "")), "node_type": str(node.get("node_type", "qemu")), "console": str(node.get("console", "telnet"))}
