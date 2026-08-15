"""Core designer test."""
from designers.topology.topology_designer import TopologyDesigner
def test_topology(): assert TopologyDesigner().design({"fault_domain_members":[["a"]]})["fault_domains"]
