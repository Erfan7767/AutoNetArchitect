import io
import logging

from log_redaction.secure_logger import SecureLogger


def test_secure_logger_redacts_message_and_audit_payload():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = SecureLogger("secure-test")
    logger.logger.setLevel(logging.DEBUG)
    logger.add_handler(handler)
    logger.info("connecting with password=%s", "cleartext")
    logger.audit("credential_event", {"password": "cleartext", "reference": "secret://device/password"})
    output = stream.getvalue()
    assert "cleartext" not in output
    assert "secret://device/password" in output
    assert "<REDACTED>" in output


def test_secure_logger_rejects_raw_secret_as_reference():
    logger = SecureLogger("secure-reference-test")
    try:
        logger.safe_reference("raw-secret")
    except ValueError:
        return
    raise AssertionError("raw values must not be accepted as secure references")
