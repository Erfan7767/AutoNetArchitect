"""Core designer test."""
from designers.qos.qos_designer import QoSDesigner
def test_qos(): assert QoSDesigner().design({})["platform"]=="agnostic"
