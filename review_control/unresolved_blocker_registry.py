"""Registry for formal unresolved blockers."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .no_go_policy import BlockerClass, NoGoBlocker


class BlockerRegistry(BaseDesigner):
    """Maintain active and resolved no-go blockers."""

    def __init__(self) -> None:
        """Initialize an empty blocker registry."""
        super().__init__("BlockerRegistry")
        self._blockers: dict[str, NoGoBlocker] = {}
        self.record_decision("blocker_registry_policy", "unresolved_blocker_is_formal_no_go", "blockers are first-class release controls and not warning text")

    def open(self, blocker: NoGoBlocker) -> NoGoBlocker:
        """Open a blocker and reject duplicate active identifiers."""
        existing = self._blockers.get(blocker.blocker_id)
        if existing is not None and not existing.resolved:
            raise ValueError(f"active blocker already exists: {blocker.blocker_id}")
        self._blockers[blocker.blocker_id] = blocker.model_copy(update={"resolved": False})
        self.record_decision(f"blocker_open:{blocker.blocker_id}", "open", blocker.blocking_reason)
        return self._blockers[blocker.blocker_id]

    def resolve(self, blocker_id: str, *, resolution_reference: str, evidence_ids: Iterable[str] = ()) -> NoGoBlocker:
        """Resolve a blocker only with a reference and evidence."""
        if not resolution_reference.strip():
            raise ValueError("blocker resolution reference is mandatory")
        evidence = tuple(dict.fromkeys(str(item) for item in evidence_ids))
        if not evidence:
            raise ValueError("blocker resolution requires evidence_ids")
        current = self._blockers[blocker_id]
        updated = current.model_copy(update={"resolved": True, "resolution_reference": resolution_reference, "evidence_ids": tuple(dict.fromkeys(current.evidence_ids + evidence))})
        self._blockers[blocker_id] = updated
        self.record_decision(f"blocker_resolve:{blocker_id}", "resolved", "blocker resolution is retained with reference and evidence")
        return updated

    def get(self, blocker_id: str) -> NoGoBlocker:
        """Return one blocker."""
        return self._blockers[blocker_id]

    def active(self, *, stage: str | None = None) -> tuple[NoGoBlocker, ...]:
        """Return unresolved blockers optionally filtered by affected stage."""
        return tuple(item for item in self._blockers.values() if not item.resolved and (stage is None or item.affected_stage == stage))

    def all(self) -> tuple[NoGoBlocker, ...]:
        """Return all blockers in stable order."""
        return tuple(self._blockers[key] for key in sorted(self._blockers))
