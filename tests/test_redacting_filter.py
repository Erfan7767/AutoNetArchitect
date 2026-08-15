import logging

from log_redaction.redacting_filter import RedactingFilter


def test_redacting_filter_hides_sensitive_text_and_preserves_reference():
    filter_instance = RedactingFilter()
    text = "password=cleartext token=abc123 secret://device/password Authorization: Bearer raw-token"
    redacted = filter_instance.redact_text(text)
    assert "cleartext" not in redacted
    assert "abc123" not in redacted
    assert "raw-token" not in redacted
    assert "secret://device/password" in redacted


def test_redacting_filter_sanitizes_nested_values_and_pem():
    data = {"username": "admin", "password": "cleartext", "nested": {"api_key": "raw-key"}, "reference": "secret://api-key"}
    sanitized = RedactingFilter.sanitize_value(data)
    assert sanitized["password"] == "<REDACTED>"
    assert sanitized["nested"]["api_key"] == "<REDACTED>"
    assert sanitized["reference"] == "secret://api-key"
    pem = "-----BEGIN PRIVATE KEY-----\nprivate-material\n-----END PRIVATE KEY-----"
    assert "private-material" not in RedactingFilter.redact_text(pem)
