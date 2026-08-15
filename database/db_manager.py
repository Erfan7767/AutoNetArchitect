"""Optional SQLite backend for local-first project persistence."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator

from .db_models import DatabaseHealth, MigrationRecord, ProjectRow


class DatabaseError(RuntimeError):
    """Raised when an optional database operation fails."""


class DBManager:
    """Manage an optional SQLite store without making it the only source of truth."""

    SCHEMA_VERSION = "1.0"

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.initialize()

    @property
    def enabled(self) -> bool:
        """Return whether SQLite persistence is enabled."""
        return self.path is not None

    def initialize(self) -> None:
        """Create the local SQLite schema idempotently."""
        if not self.enabled:
            return
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration_id TEXT PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    schema_version TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

    def save_project(self, row: ProjectRow) -> None:
        """Atomically insert or replace a project row."""
        self._require_enabled()
        try:
            with self._connect() as connection:
                connection.execute("BEGIN")
                connection.execute("""INSERT INTO projects(project_id, schema_version, payload_json, checksum, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(project_id) DO UPDATE SET schema_version=excluded.schema_version,
                    payload_json=excluded.payload_json, checksum=excluded.checksum, updated_at=excluded.updated_at""", (row.project_id, row.schema_version, row.payload_json, row.checksum, row.updated_at))
                connection.commit()
        except sqlite3.DatabaseError as exc:
            raise DatabaseError("could not save project row") from exc

    def load_project(self, project_id: str) -> ProjectRow | None:
        """Load one project row or return None."""
        self._require_enabled()
        with self._connect() as connection:
            cursor = connection.execute("SELECT project_id, schema_version, payload_json, checksum, updated_at FROM projects WHERE project_id = ?", (project_id,))
            row = cursor.fetchone()
        return ProjectRow(*row) if row else None

    def delete_project(self, project_id: str) -> None:
        """Delete one project row."""
        self._require_enabled()
        with self._connect() as connection:
            connection.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))

    def list_project_ids(self) -> tuple[str, ...]:
        """Return project IDs in deterministic order."""
        self._require_enabled()
        with self._connect() as connection:
            rows = connection.execute("SELECT project_id FROM projects ORDER BY project_id").fetchall()
        return tuple(str(row[0]) for row in rows)

    def record_migration(self, record: MigrationRecord) -> None:
        """Record one applied migration idempotently."""
        self._require_enabled()
        with self._connect() as connection:
            connection.execute("INSERT OR REPLACE INTO schema_migrations(migration_id, checksum, applied_at) VALUES (?, ?, ?)", (record.migration_id, record.checksum, record.applied_at))

    def migrations(self) -> tuple[MigrationRecord, ...]:
        """Return applied migrations."""
        self._require_enabled()
        with self._connect() as connection:
            rows = connection.execute("SELECT migration_id, checksum, applied_at FROM schema_migrations ORDER BY migration_id").fetchall()
        return tuple(MigrationRecord(*row) for row in rows)

    def health(self) -> DatabaseHealth:
        """Return a non-throwing database health snapshot."""
        if not self.enabled:
            return DatabaseHealth(False, None, None, 0, True, "optional database disabled")
        try:
            with self._connect() as connection:
                count = int(connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0])
            return DatabaseHealth(True, str(self.path), self.SCHEMA_VERSION, count, True, "sqlite backend healthy")
        except sqlite3.DatabaseError as exc:
            return DatabaseHealth(True, str(self.path), None, 0, False, str(exc))

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Yield a transactional SQLite connection."""
        self._require_enabled()
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        if self.path is None:
            raise DatabaseError("SQLite backend is disabled")
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise DatabaseError("SQLite backend is disabled")
