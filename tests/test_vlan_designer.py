"""Core designer test."""
from designers.vlan.vlan_designer import VLANDesigner
def test_special_vlans(): assert any(v["name"]=="quarantine" for v in VLANDesigner().design({"enable_quarantine":True})["vlans"])
