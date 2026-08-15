"""Structured and terminal-friendly output formatting for the CLI."""
from __future__ import annotations

from dataclasses import is_dataclass, asdict
import json
import os
from typing import Any, Mapping, Sequence

from log_redaction.redacting_filter import RedactingFilter


class OutputFormatError(ValueError):
    """Raised when an unsupported output format is requested."""


class OutputFormatter:
    """Render secret-safe result mappings in text, JSON, YAML, or table form."""

    FORMATS = frozenset({"text", "json", "yaml", "table"})

    def __init__(self, output_format: str = "text", *, no_color: bool = False, quiet: bool = False) -> None:
        """Create a formatter with explicit output settings."""
        normalized = output_format.lower()
        if normalized not in self.FORMATS:
            raise OutputFormatError(f"unsupported output format: {output_format}")
        self.output_format = normalized
        self.no_color = no_color or not os.isatty(1)
        self.quiet = quiet

    def render(self, value: Any, *, status: str | None = None, message: str | None = None) -> str:
        """Return a complete formatted string."""
        safe = self._normalize(RedactingFilter.sanitize_value(value))
        if self.quiet and status in {"success", "completed", "listed", "loaded", "delegated", "created", "opened"}:
            return ""
        if self.output_format == "json":
            body: Any = safe
            if message is not None or status is not None:
                body = {"status": status, "message": message, "data": safe}
            return json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False, default=str)
        if self.output_format == "yaml":
            body: Any = safe
            if message is not None or status is not None:
                body = {"status": status, "message": message, "data": safe}
            return self._yaml(body)
        if self.output_format == "table":
            return self._table(safe)
        return self._text(safe, status=status, message=message)

    def emit(self, value: Any, *, status: str | None = None, message: str | None = None) -> None:
        """Print a formatted value exactly once."""
        rendered = self.render(value, status=status, message=message)
        if rendered:
            print(rendered)

    def _text(self, value: Any, *, status: str | None, message: str | None) -> str:
        """Render human-readable output without requiring a terminal package."""
        lines: list[str] = []
        if status:
            lines.append(self._status(status))
        if message:
            lines.append(message)
        if isinstance(value, Mapping):
            for key, item in value.items():
                if isinstance(item, (dict, list, tuple)):
                    lines.append(f"{key}:")
                    lines.extend(f"  {line}" for line in self._text(item, status=None, message=None).splitlines())
                else:
                    lines.append(f"{key}: {item}")
        elif isinstance(value, (list, tuple)):
            lines.extend(f"- {item}" for item in value)
        else:
            lines.append(str(value))
        return "\n".join(lines)

    def _table(self, value: Any) -> str:
        """Render mappings or row lists as a deterministic ASCII table."""
        if isinstance(value, Mapping):
            rows = [{"key": key, "value": item} for key, item in value.items()]
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            rows = [dict(item) if isinstance(item, Mapping) else {"value": item} for item in value]
        else:
            rows = [{"value": value}]
        if not rows:
            return "(empty)"
        headers = tuple(dict.fromkeys(key for row in rows for key in row))
        widths = {header: max(len(header), *(len(str(row.get(header, ""))) for row in rows)) for header in headers}
        separator = "+" + "+".join("-" * (widths[header] + 2) for header in headers) + "+"
        lines = [separator, "|" + "|".join(f" {header.ljust(widths[header])} " for header in headers) + "|", separator]
        lines.extend("|" + "|".join(f' {str(row.get(header, "")).ljust(widths[header])} ' for header in headers) + "|" for row in rows)
        lines.append(separator)
        return "\n".join(lines)

    def _status(self, status: str) -> str:
        """Render a status label with optional ANSI color."""
        if self.no_color:
            return f"[{status}]"
        colors = {"success": "\033[32m", "completed": "\033[32m", "error": "\033[31m", "blocked": "\033[33m", "warning": "\033[33m"}
        color = colors.get(status, "\033[36m")
        return f"{color}[{status}]\033[0m"

    @staticmethod
    def _normalize(value: Any) -> Any:
        """Convert dataclasses and tuples to JSON-compatible structures."""
        if is_dataclass(value) and not isinstance(value, type):
            return OutputFormatter._normalize(asdict(value))
        if isinstance(value, Mapping):
            return {str(key): OutputFormatter._normalize(item) for key, item in value.items()}
        if isinstance(value, tuple):
            return [OutputFormatter._normalize(item) for item in value]
        if isinstance(value, list):
            return [OutputFormatter._normalize(item) for item in value]
        return value

    @staticmethod
    def _yaml(value: Any, indent: int = 0) -> str:
        """Serialize basic JSON-compatible structures as dependency-free YAML."""
        prefix = " " * indent
        if isinstance(value, Mapping):
            lines: list[str] = []
            for key, item in value.items():
                if isinstance(item, (Mapping, list, tuple)):
                    lines.append(f"{prefix}{key}:")
                    lines.append(OutputFormatter._yaml(item, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: {OutputFormatter._yaml_scalar(item)}")
            return "\n".join(line for line in lines if line != "")
        if isinstance(value, (list, tuple)):
            lines = []
            for item in value:
                if isinstance(item, Mapping):
                    lines.append(f"{prefix}-")
                    lines.append(OutputFormatter._yaml(item, indent + 2))
                elif isinstance(item, (list, tuple)):
                    lines.append(f"{prefix}-")
                    lines.append(OutputFormatter._yaml(item, indent + 2))
                else:
                    lines.append(f"{prefix}- {OutputFormatter._yaml_scalar(item)}")
            return "\n".join(lines)
        return f"{prefix}{OutputFormatter._yaml_scalar(value)}"

    @staticmethod
    def _yaml_scalar(value: Any) -> str:
        """Render one safe scalar."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return json.dumps(str(value), ensure_ascii=False)
