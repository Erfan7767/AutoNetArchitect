"""Secure logging with redaction support."""
import logging
from .string_utils import redact_text
class RedactingFilter(logging.Filter):
    """Redact configured secrets from log messages."""
    def __init__(self, secrets: list[str] | None = None) -> None: super().__init__(); self.secrets = [s for s in (secrets or []) if s]
    def filter(self, record: logging.LogRecord) -> bool:
        """Redact message text in place and allow the record."""
        message = record.getMessage()
        for secret in self.secrets: message = redact_text(message, secret)
        record.msg, record.args = message, (); return True
class SecureLogger:
    """Factory for loggers with redaction filters."""
    def __init__(self, name: str, secrets: list[str] | None = None) -> None: self.logger = logging.getLogger(name); self.logger.addFilter(RedactingFilter(secrets))
    def info(self, message: str, *args: object) -> None: """Log an informational message."""; self.logger.info(message, *args)
    def error(self, message: str, *args: object) -> None: """Log an error message."""; self.logger.error(message, *args)
