"""Helpers for semantic diagram views that are not raw physical cabling."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def records(value: Any) -> list[Mapping[str, Any]]:
    """Normalize a source value into mapping records."""
    if isinstance(value, Mapping):
        for key in ("records", "items", "nodes", "links", "tunnels", "areas", "vlans", "dependencies", "rules"):
            nested = value.get(key)
            if isinstance(nested, Sequence) and not isinstance(nested, (str, bytes)):
                return [item for item in nested if isinstance(item, Mapping)]
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def source_records(artifacts: Mapping[str, Any], keys: tuple[str, ...]) -> list[Mapping[str, Any]]:
    """Collect records from an ordered list of explicit artifact keys."""
    result: list[Mapping[str, Any]] = []
    for key in keys:
        result.extend(records(artifacts.get(key)))
    return result


def text(record: Mapping[str, Any], *keys: str) -> str | None:
    """Return first non-empty scalar value."""
    for key in keys:
        value = record.get(key)
        if value is not None and not isinstance(value, (dict, list, tuple, set)) and str(value).strip():
            return str(value).strip()
    return None
