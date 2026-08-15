"""Shared fixtures for documentation tests."""
from __future__ import annotations

from documentation.doc_models import DocumentType, ResolvedData
from documentation.doc_data_resolver import DocDataResolver
from documentation.doc_section_registry import DocumentSectionRegistry


def artifacts() -> dict:
    return {
        "project_metadata": {"project_id": "p-1", "name": "Network", "customer": "Supplied Customer", "secret": "raw-value"},
        "sot_basis": {"DESIGN": "sot:design:p-1", "DEPLOYMENT": "sot:deployment:p-1"},
        "evidence_basis": ["evidence:design:1"],
        "source_timestamps": ["2026-08-01T00:00:00+00:00"],
        "requirements": {"business": ["availability"], "technical": ["segmentation"]},
        "design": {"topology": "supplied"},
        "security_design": {"zones": [{"name": "staff"}]},
        "equipment": [{"device": "sw-01", "model": "supplied"}],
        "bom": [{"part": "supplied", "quantity": 1}, {"part": "SFP", "quantity": 2}],
        "governance": {"assumptions": [], "risks": []},
        "physical_design": [{"site": "HQ", "rack": "R1"}],
        "interface_assignment": [{"device": "sw-01", "interface": "Gi1/0/1"}],
        "ip_design": [{"network": "10.0.0.0/24", "vlan": 10}],
        "vlan_design": [{"id": 10, "name": "staff"}],
        "routing_design": [{"protocol": "OSPF", "area": "0"}],
        "routing_security": {"routing": "OSPF", "security": "segmentation"},
        "config_artifacts": [{"device": "sw-01", "config": "interface reference only"}],
        "nat_design": [{"rule": "supplied"}],
        "wireless_design": [{"ssid": "staff"}],
        "wireless_evidence": [{"type": "survey", "status": "supplied"}],
        "qos_design": [{"class": "voice"}],
        "wan_design": [{"site": "HQ", "handoff": "PENDING: human input"}],
        "vpn_design": [{"tunnel": "supplied"}],
        "dr_design": {"rpo": "supplied", "rto": "supplied"},
        "sow": {"scope": ["supplied"]},
        "atp": {"tests": [{"id": "T-1", "result": "PENDING"}]},
        "as_built": {"state": "as-designed"},
        "operational_state": [{"device": "sw-01", "status": "observed"}],
        "handover": {"index": ["HLD"]},
        "operations": [{"procedure": "backup"}],
        "incident_response": [{"procedure": "outage"}],
        "troubleshooting": [{"symptom": "no access"}],
        "change_management": [{"change": "supplied"}],
        "compliance": [{"framework": "technical assessment"}],
        "inventory": [{"device": "sw-01"}],
        "decisions": [{"id": "D-1", "rationale": "supplied"}],
        "assumptions": [{"id": "A-1", "description": "supplied"}],
        "risks": [{"id": "R-1", "description": "supplied"}],
        "voice_design": [{"codec": "supplied"}],
        "nac_design": [{"method": "802.1X"}],
        "traffic_analysis": [{"metric": "utilization", "value": "supplied"}],
    }


def resolved(document_type: DocumentType) -> ResolvedData:
    registry = DocumentSectionRegistry()
    return DocDataResolver().resolve(document_type=document_type, artifacts=artifacts(), registry=registry)
