"""Explicit project schema migration contracts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class SchemaMigrationError(RuntimeError):
    """Raised when a project cannot be migrated safely."""


@dataclass(frozen=True)
class MigrationStep:
    """One deterministic schema migration step."""

    from_version: str
    to_version: str
    migrate: Callable[[dict[str, Any]], dict[str, Any]]
    description: str


class SchemaMigrator:
    """Apply only registered, deterministic migrations."""

    CURRENT_VERSION = "1.0.0"

    def __init__(self, steps: tuple[MigrationStep, ...] | None = None) -> None:
        self._steps = {(step.from_version, step.to_version): step for step in (steps or self.default_steps())}

    @staticmethod
    def default_steps() -> tuple[MigrationStep, ...]:
        """Return the built-in V1 migration path."""
        def migrate_090_to_100(payload: dict[str, Any]) -> dict[str, Any]:
            migrated = dict(payload)
            migrated.setdefault("project_metadata", {})
            migrated.setdefault("assumptions", [])
            migrated.setdefault("decisions", [])
            migrated.setdefault("evidence_ids", [])
            return migrated
        def migrate_10_to_100(payload: dict[str, Any]) -> dict[str, Any]:
            return dict(payload)
        return (
            MigrationStep("0.9.0", "1.0.0", migrate_090_to_100, "Add V1 project metadata, assumptions, decisions, and evidence fields."),
            MigrationStep("1.0", "1.0.0", migrate_10_to_100, "Normalize short V1 schema version."),
        )

    def migrate(self, payload: dict[str, Any], from_version: str) -> tuple[dict[str, Any], tuple[str, ...]]:
        """Migrate payload to current schema or raise instead of guessing."""
        if not isinstance(payload, dict):
            raise SchemaMigrationError("project payload must be an object")
        if from_version == self.CURRENT_VERSION:
            return dict(payload), ()
        if from_version not in {step.from_version for step in self._steps.values()}:
            raise SchemaMigrationError(f"no migration path from schema {from_version}")
        current = from_version
        migrated = dict(payload)
        applied: list[str] = []
        visited: set[str] = set()
        while current != self.CURRENT_VERSION:
            if current in visited:
                raise SchemaMigrationError("migration cycle detected")
            visited.add(current)
            candidates = [step for step in self._steps.values() if step.from_version == current]
            if len(candidates) != 1:
                raise SchemaMigrationError(f"migration path is ambiguous or missing from schema {current}")
            step = candidates[0]
            migrated = step.migrate(migrated)
            current = step.to_version
            applied.append(f"{step.from_version}->{step.to_version}")
        return migrated, tuple(applied)
