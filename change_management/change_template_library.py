"""Reusable change templates for common network operations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .change_models import ChangeRequest, ImplementationPlan, RollbackPlan, RiskAssessment, TestPlan


@dataclass(frozen=True)
class ChangeTemplate:
    """Template skeleton for a recurring change."""

    template_id: str
    title: str
    description: str
    default_category: str
    default_risk_level: str
    variables: tuple[str, ...]
    risk_skeleton: RiskAssessment
    implementation_skeleton: ImplementationPlan
    rollback_skeleton: RollbackPlan
    verification_skeleton: TestPlan

    def to_dict(self) -> dict[str, Any]:
        """Serialize template skeleton."""
        return {"template_id": self.template_id, "title": self.title, "description": self.description, "default_category": self.default_category, "default_risk_level": self.default_risk_level, "variables": list(self.variables), "risk_skeleton": self.risk_skeleton.to_dict(), "implementation_skeleton": self.implementation_skeleton.to_dict(), "rollback_skeleton": self.rollback_skeleton.to_dict(), "verification_skeleton": self.verification_skeleton.to_dict()}


class ChangeTemplateLibrary:
    """Local template library with no external ITSM dependency."""

    TEMPLATE_IDS = ("add_vlan", "add_access_port", "modify_acl", "add_static_route", "update_ntp", "add_snmp_community", "firmware_upgrade", "add_vpn_tunnel")

    def __init__(self) -> None:
        """Create built-in template skeletons."""
        self._templates = {template_id: self._build(template_id) for template_id in self.TEMPLATE_IDS}

    def get(self, template_id: str) -> ChangeTemplate:
        """Return a template by ID."""
        try:
            return self._templates[template_id]
        except KeyError as exc:
            raise KeyError(f"change template not found: {template_id}") from exc

    def list(self) -> tuple[ChangeTemplate, ...]:
        """Return templates in deterministic order."""
        return tuple(self._templates[key] for key in sorted(self._templates))

    def apply(self, template_id: str, request: ChangeRequest, variables: Mapping[str, str] | None = None) -> ChangeRequest:
        """Apply safe metadata skeletons to a request without inventing commands."""
        template = self.get(template_id)
        variables = variables or {}
        missing = tuple(variable for variable in template.variables if variable not in variables)
        if missing:
            request.assumptions.append({"key": f"template:{template_id}:variables", "value": missing, "rationale": "template variables require human-supplied values", "requires_validation": True})
        request.change_category = template.default_category
        request.risk_assessment = template.risk_skeleton
        request.implementation_plan = template.implementation_skeleton
        request.rollback_plan = template.rollback_skeleton
        request.test_plan = template.verification_skeleton
        request.assumptions.append({"key": f"template:{template_id}", "value": "applied", "rationale": "template skeleton is not an execution command set", "requires_validation": True})
        return request

    @staticmethod
    def _build(template_id: str) -> ChangeTemplate:
        """Build one bounded skeleton."""
        names = {"add_vlan": ("Add VLAN", "configuration", ("vlan_id", "vlan_name", "device_id")), "add_access_port": ("Add access port", "configuration", ("device_id", "interface", "vlan_id")), "modify_acl": ("Modify ACL", "security", ("device_id", "acl_name", "rule_intent")), "add_static_route": ("Add static route", "connectivity", ("device_id", "prefix", "next_hop")), "update_ntp": ("Update NTP", "configuration", ("device_id", "ntp_reference")), "add_snmp_community": ("Add read-only SNMP community", "security", ("device_id", "community_reference")), "firmware_upgrade": ("Firmware upgrade", "software", ("device_id", "target_version", "image_evidence")), "add_vpn_tunnel": ("Add VPN tunnel", "connectivity", ("device_id", "peer_reference", "tunnel_intent"))}
        title, category, variables = names[template_id]
        return ChangeTemplate(template_id, title, f"Template skeleton for {title.lower()}", category, "low" if template_id in {"add_vlan", "add_access_port", "update_ntp", "add_snmp_community"} else "medium", variables, RiskAssessment(0.0, "low"), ImplementationPlan(prerequisites=("human variables supplied", "config validator evidence supplied")), RollbackPlan(), TestPlan(checks=("post-change verification",), required_verification_types=("command_verification",)))
