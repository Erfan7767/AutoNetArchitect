from documentation.doc_redaction_engine import DocRedactionEngine
from documentation.doc_models import RedactionLevel

def test_redaction_removes_secret_and_masks_strict_identifiers():
    value = {"password": "secret-value", "text": "serial: ABC123 10.1.2.3"}
    redacted, findings, applied = DocRedactionEngine().redact(value, RedactionLevel.STRICT)
    assert redacted["password"] == "[REDACTED]"
    assert "10.1.2.3" not in redacted["text"]
    assert findings and applied
