"""Technical compliance scope and control catalogs."""
from __future__ import annotations

from .compliance_models import ComplianceFramework, ControlDefinition, ComplianceScope, EvidenceDomain


def default_scope(framework: ComplianceFramework, *, framework_version: str | None = None, organization_scope: str | None = None, system_scope: str | None = None, authoritative_obligations_supplied: bool = False) -> ComplianceScope:
    """Build a conservative technical-only scope."""
    return ComplianceScope(framework=framework, framework_version=framework_version, organization_scope=organization_scope, system_scope=system_scope, assessment_purpose="technical_network_control_assessment", authoritative_obligations_supplied=authoritative_obligations_supplied, disclaimer="Technical network control assessment only. It does not assess non-network safeguards, privacy/legal interpretation, organizational governance completeness, audit opinion, certification, accreditation, or full regulatory readiness.")


def controls_for(framework: ComplianceFramework) -> tuple[ControlDefinition, ...]:
    """Return a bounded technical control catalog for a framework."""
    common = {
        "access": ControlDefinition(control_id=f"{framework.value}.NET-ACCESS", title="Network access control", technical_objective="Privileged and administrative network access is governed, separated, and traceable.", required_evidence_domains=[EvidenceDomain.DESIGN, EvidenceDomain.CONFIGURATION, EvidenceDomain.OPERATIONAL], implementation_examples=["AAA/RBAC design", "management-plane ACLs", "MFA or compensating control evidence"]),
        "segmentation": ControlDefinition(control_id=f"{framework.value}.NET-SEGMENT", title="Network segmentation", technical_objective="Sensitive or regulated zones have an explicit boundary and tested permitted/denied reachability.", required_evidence_domains=[EvidenceDomain.DESIGN, EvidenceDomain.CONFIGURATION, EvidenceDomain.OPERATIONAL], implementation_examples=["VRF/VLAN/security-zone design", "firewall/ACL policy", "reachability verification"]),
        "logging": ControlDefinition(control_id=f"{framework.value}.NET-LOG", title="Network audit logging and monitoring", technical_objective="Relevant network and security events are logged, time-aligned, retained, and reviewable.", required_evidence_domains=[EvidenceDomain.DESIGN, EvidenceDomain.CONFIGURATION, EvidenceDomain.OPERATIONAL], implementation_examples=["syslog/SIEM design", "NTP design", "observed log delivery and retention evidence"]),
        "change": ControlDefinition(control_id=f"{framework.value}.NET-CHANGE", title="Controlled network change", technical_objective="Network changes are approved, traceable, backed up, and verified.", required_evidence_domains=[EvidenceDomain.DESIGN, EvidenceDomain.CONFIGURATION, EvidenceDomain.OPERATIONAL], implementation_examples=["change approval", "configuration backup", "post-change verification"]),
        "resilience": ControlDefinition(control_id=f"{framework.value}.NET-RESILIENCE", title="Network availability and recovery", technical_objective="Critical network services have documented resilience, backup, recovery, and verification evidence.", required_evidence_domains=[EvidenceDomain.DESIGN, EvidenceDomain.OPERATIONAL], implementation_examples=["failure-domain design", "backup/restore evidence", "DR test evidence"]),
    }
    if framework == ComplianceFramework.CIS_BENCHMARK:
        return tuple(common[key] for key in ("access", "logging", "change")) + (ControlDefinition(control_id="cis_benchmark.NET-HARDEN", title="Network device hardening", technical_objective="Unnecessary services and insecure management paths are disabled or controlled according to an identified benchmark version.", required_evidence_domains=[EvidenceDomain.CONFIGURATION, EvidenceDomain.OPERATIONAL], implementation_examples=["SSH-only management", "AAA", "disabled unused services", "secure SNMP configuration"]),)
    if framework == ComplianceFramework.PCI_DSS:
        return tuple(common[key] for key in ("access", "segmentation", "logging", "change", "resilience"))
    if framework == ComplianceFramework.HIPAA:
        return tuple(common[key] for key in ("access", "segmentation", "logging", "change", "resilience"))
    if framework == ComplianceFramework.ISO_27001:
        return tuple(common[key] for key in ("access", "segmentation", "logging", "change", "resilience"))
    return tuple(common[key] for key in ("access", "segmentation", "logging", "change", "resilience"))
