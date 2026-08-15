"""Local-first atomic project persistence with checksum and migration support."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from database.db_manager import DBManager
from database.db_models import ProjectRow
from .integrity_checker import IntegrityChecker, IntegrityError
from .schema_migrations import SchemaMigrator


class PersistenceError(RuntimeError):
    """Raised when a project cannot be saved or loaded safely."""


@dataclass(frozen=True)
class PersistenceResult:
    """Result of a project save or load operation."""

    project_id: str
    schema_version: str
    checksum: str
    migrated_from: str | None = None
    migrations_applied: tuple[str, ...] = ()
    source: str = "local_file"


class ProjectPersistence:
    """Persist project dictionaries locally first and optionally mirror them to SQLite."""

    CURRENT_SCHEMA_VERSION = SchemaMigrator.CURRENT_VERSION

    def __init__(self, root: str | Path, db_manager: DBManager | None = None, migrator: SchemaMigrator | None = None) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_manager = db_manager
        self.migrator = migrator or SchemaMigrator()

    def path_for(self, project_id: str) -> Path:
        """Return a safe project envelope path."""
        self._validate_project_id(project_id)
        return self.root / f"{project_id}.project.json"

    def save(self, project_id: str, payload: dict[str, Any], mirror_to_db: bool = True) -> PersistenceResult:
        """Atomically save a project and optionally mirror the canonical envelope to SQLite."""
        self._validate_project_id(project_id)
        if not isinstance(payload, dict):
            raise PersistenceError("project payload must be a dictionary")
        body = dict(payload)
        body.setdefault("project_id", project_id)
        if body["project_id"] != project_id:
            raise PersistenceError("payload project_id does not match save project_id")
        body["schema_version"] = self.CURRENT_SCHEMA_VERSION
        envelope = {
            "project_id": project_id,
            "schema_version": self.CURRENT_SCHEMA_VERSION,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "checksum_algorithm": IntegrityChecker.ALGORITHM,
            "payload": body,
        }
        envelope["checksum"] = IntegrityChecker.envelope_checksum(envelope)
        target = self.path_for(project_id)
        temporary = target.with_suffix(target.suffix + ".tmp")
        try:
            temporary.write_text(json.dumps(envelope, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
            with temporary.open("r", encoding="utf-8") as handle:
                persisted = json.load(handle)
            IntegrityChecker.verify_envelope(persisted)
            temporary.replace(target)
            if mirror_to_db and self.db_manager is not None and self.db_manager.enabled:
                self.db_manager.save_project(ProjectRow(project_id, envelope["schema_version"], json.dumps(envelope["payload"], sort_keys=True, ensure_ascii=False), envelope["checksum"], envelope["saved_at"]))
        except (OSError, ValueError, TypeError) as exc:
            if temporary.exists():
                temporary.unlink()
            raise PersistenceError("atomic project save failed") from exc
        return PersistenceResult(project_id, self.CURRENT_SCHEMA_VERSION, envelope["checksum"], None, (), "local_file")

    def load(self, project_id: str, migrate: bool = True, fallback_to_db: bool = True) -> tuple[dict[str, Any], PersistenceResult]:
        """Load a project from local file first, verify integrity, and migrate explicitly."""
        self._validate_project_id(project_id)
        target = self.path_for(project_id)
        source = "local_file"
        envelope: dict[str, Any]
        if target.exists():
            try:
                envelope = json.loads(target.read_text(encoding="utf-8"))
                IntegrityChecker.verify_envelope(envelope)
            except (OSError, ValueError, TypeError, IntegrityError) as exc:
                raise PersistenceError("local project envelope is corrupt or unreadable") from exc
        elif fallback_to_db and self.db_manager is not None and self.db_manager.enabled:
            row = self.db_manager.load_project(project_id)
            if row is None:
                raise FileNotFoundError(f"project not found: {project_id}")
            try:
                payload = json.loads(row.payload_json)
            except (ValueError, TypeError) as exc:
                raise PersistenceError("database project payload is invalid JSON") from exc
            envelope = {"project_id": row.project_id, "schema_version": row.schema_version, "saved_at": row.updated_at, "checksum_algorithm": IntegrityChecker.ALGORITHM, "payload": payload, "checksum": row.checksum}
            if IntegrityChecker.envelope_checksum(envelope) != row.checksum:
                raise PersistenceError("database project checksum mismatch")
            source = "sqlite_fallback"
        else:
            raise FileNotFoundError(f"project not found: {project_id}")
        payload = envelope.get("payload")
        if not isinstance(payload, dict):
            raise PersistenceError("project envelope payload is not a dictionary")
        version = str(envelope.get("schema_version", ""))
        migrations: tuple[str, ...] = ()
        migrated_from: str | None = None
        if version != self.CURRENT_SCHEMA_VERSION:
            if not migrate:
                raise PersistenceError(f"project schema {version} requires migration")
            migrated_from = version
            payload, migrations = self.migrator.migrate(payload, version)
            payload["project_id"] = project_id
            payload["schema_version"] = self.CURRENT_SCHEMA_VERSION
            result = self.save(project_id, payload, mirror_to_db=self.db_manager is not None and self.db_manager.enabled)
            return payload, PersistenceResult(result.project_id, result.schema_version, result.checksum, migrated_from, migrations, source)
        if payload.get("project_id", project_id) != project_id:
            raise PersistenceError("payload project_id does not match envelope")
        return payload, PersistenceResult(project_id, version, str(envelope["checksum"]), migrated_from, migrations, source)

    def exists(self, project_id: str) -> bool:
        """Return whether a local project file exists."""
        return self.path_for(project_id).exists()

    def delete(self, project_id: str, delete_db: bool = False) -> None:
        """Delete local project data and optionally the SQLite mirror."""
        target = self.path_for(project_id)
        if target.exists():
            target.unlink()
        if delete_db and self.db_manager is not None and self.db_manager.enabled:
            self.db_manager.delete_project(project_id)

    @staticmethod
    def _validate_project_id(project_id: str) -> None:
        if not isinstance(project_id, str) or not project_id or project_id in {".", ".."} or "/" in project_id or "\\" in project_id:
            raise ValueError("project_id must be a non-empty path-safe identifier")
