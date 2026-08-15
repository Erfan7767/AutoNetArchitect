"""Secure logging facade that always attaches a redaction filter."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any

from .redacting_filter import RedactingFilter


class SecureLogger:
    """Structured logger with mandatory pre-handler redaction."""

    def __init__(self, name: str, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(name)
        self.filter = RedactingFilter()
        self.logger.addFilter(self.filter)
        for handler in self.logger.handlers:
            handler.addFilter(self.filter)
        self.logger.propagate = False

    def add_handler(self, handler: logging.Handler) -> None:
        """Attach a handler with the redaction filter already installed."""
        handler.addFilter(self.filter)
        self.logger.addHandler(handler)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a redacted debug record."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a redacted info record."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a redacted warning record."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a redacted error record."""
        self.logger.error(message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a redacted exception record."""
        self.logger.exception(message, *args, **kwargs)

    def audit(self, event: str, details: dict[str, Any] | None = None, level: int = logging.INFO) -> None:
        """Emit sanitized structured audit details."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "details": RedactingFilter.sanitize_value(details or {}),
        }
        self.logger.log(level, json.dumps(payload, sort_keys=True, default=str))

    def safe_reference(self, reference: str) -> str:
        """Return a permitted secret reference and reject raw values."""
        if not isinstance(reference, str) or not reference.startswith("secret://"):
            raise ValueError("secure logger accepts secret:// references only")
        return reference
