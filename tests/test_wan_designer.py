"""Core designer test."""
from designers.wan.wan_designer import WANDesigner
def test_wan_mandatory(): assert WANDesigner().design({})["status"]=="blocked_pending_human_mandatory"
