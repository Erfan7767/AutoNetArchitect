"""Shared source artifacts for diagram tests."""
from __future__ import annotations

from diagrams.diagram_models import DiagramType
from diagrams.diagram_orchestrator import DiagramOrchestrator


def artifacts() -> dict:
    return {
        "nodes": [
            {"id": "core-1", "hostname": "core-1", "node_type": "switch_l3", "vendor": "cisco", "model": "C9300", "role": "core", "site": "HQ", "building": "HQ-1", "floor": "1"},
            {"id": "access-1", "hostname": "access-1", "node_type": "switch_l2", "vendor": "aruba", "model": "CX", "role": "access", "site": "HQ", "building": "HQ-1", "floor": "1"},
            {"id": "fw-1", "hostname": "fw-1", "node_type": "firewall", "vendor": "fortinet", "model": "FG", "role": "firewall", "site": "HQ"},
        ],
        "links": [{"id": "link-1", "source": "core-1", "target": "access-1", "edge_type": "trunk", "source_interface": "Gi1", "target_interface": "1/1/1", "bandwidth": "10G"}, {"id": "link-2", "source": "core-1", "target": "fw-1", "edge_type": "routing", "source_interface": "Gi2", "target_interface": "port1", "bandwidth": "10G"}],
        "sites": [{"id": "HQ", "name": "HQ", "node_type": "site"}],
        "buildings": [{"id": "HQ-1", "name": "HQ-1", "node_type": "building", "site": "HQ"}],
        "racks": [{"id": "rack-1", "name": "Rack 1", "node_type": "rack", "site": "HQ", "ru_capacity": 42}],
        "vlans": [{"id": "10", "vlan_id": 10, "name": "Staff", "subnet": "10.10.0.0/24", "devices": ["core-1", "access-1"]}],
        "routing_domains": [{"id": "area-0", "area_id": "0", "protocol": "OSPF", "name": "Backbone"}],
        "vpn_tunnels": [{"id": "vpn-1", "source": "core-1", "target": "fw-1", "edge_type": "vpn", "tunnel_type": "IPSec", "source_interface": "tun0", "target_interface": "tun0"}],
        "dr_sites": [{"id": "DR", "name": "DR", "node_type": "site"}],
        "access_points": [{"id": "ap-1", "hostname": "ap-1", "node_type": "access_point", "site": "HQ", "building": "HQ-1", "floor": "1", "status": "pending"}],
        "wireless_evidence": [{"type": "heuristic", "status": "not_surveyed"}],
        "ip_allocations": [{"id": "root", "cidr": "10.0.0.0/8"}, {"id": "hq", "cidr": "10.10.0.0/16", "parent_id": "root"}, {"id": "staff", "cidr": "10.10.0.0/24", "parent_id": "hq"}],
        "dependencies": [{"id": "dns", "name": "DNS", "node_type": "service", "depends_on": ["ntp"]}, {"id": "ntp", "name": "NTP", "node_type": "service", "depends_on": []}],
        "sot_basis": {"DESIGN": "sot:design:p-1"},
        "evidence_basis": ["evidence:design:1"],
    }


def model(diagram_type: DiagramType):
    return DiagramOrchestrator().model(__import__('diagrams').DiagramRequest(diagram_type=diagram_type, project_id="p-1", output_path="/tmp/diagram-test.svg"), artifacts())
