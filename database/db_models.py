"""Typed records used by the optional SQLite persistence backend."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ProjectRow:
    """One persisted project row; payload is canonical JSON text."""

    project_id: str
    schema_version: str
    payload_json: str
    checksum: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize database row metadata."""
        return asdict(self)


@dataclass(frozen=True)
class MigrationRecord:
    """One applied database migration."""

    migration_id: str
    checksum: str
    applied_at: str


@dataclass(frozen=True)
class DatabaseHealth:
    """Operational status of the optional database backend."""

    enabled: bool
    path: str | None
    schema_version: str | None
    project_count: int
    healthy: bool
    reason: str
