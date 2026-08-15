"""Core designer test."""
from designers.ip.ip_designer import IPDesigner
def test_ip(): assert IPDesigner().design({"growth_percent":30})["growth_percent"]==30
