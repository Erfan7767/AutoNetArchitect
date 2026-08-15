"""Compatibility adapter to the mandatory secure logging redactor."""

from log_redaction.redacting_filter import RedactingFilter


class SettingsEncryptor:
    """Delegate settings redaction to the central secure logging layer."""

    def redact(self, values: dict[str, object]) -> dict[str, object]:
        """Return a recursively redacted copy without resolving references."""
        return RedactingFilter.sanitize_value(values)
