"""Core designer test."""
from designers.security.security_designer import SecurityDesigner
def test_security(): assert SecurityDesigner().design({"intents":[{"source":"a","destination":"b"}]})["rules"]
