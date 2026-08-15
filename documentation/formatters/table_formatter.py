"""Table normalization utilities for document renderers."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class TableFormatter:
    """Normalize tabular records into stable columns and rows."""

    def normalize(self, value: Any) -> tuple[list[str], list[list[str]]]:
        """Return deterministic headers and stringified rows."""
        if isinstance(value, Mapping):
            records = [value]
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            records = list(value)
        else:
            return ["Value"], [[self._stringify(value)]]
        if not records:
            return ["Value"], []
        if all(isinstance(item, Mapping) for item in records):
            headers = sorted({str(key) for item in records for key in item.keys()})
            rows = [[self._stringify(item.get(header, "")) for header in headers] for item in records]
            return headers, rows
        return ["Value"], [[self._stringify(item)] for item in records]

    def markdown(self, value: Any) -> str:
        """Render a value as a Markdown pipe table."""
        headers, rows = self.normalize(value)
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
        lines.extend("| " + " | ".join(row) + " |" for row in rows)
        return "\n".join(lines)

    @staticmethod
    def _stringify(value: Any) -> str:
        """Produce readable scalar text without leaking object representations."""
        if value is None:
            return "PENDING: value not supplied"
        if isinstance(value, (dict, list, tuple)):
            return str(value)
        return str(value)
