"""Evidence-only handoff for a human-authorized local backup captured by the site agent."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from operations.backup_manager import BackupManager

from .models import DiscoveryResult, DiscoveryState
from .scope import AuthorizedScope


class BackupCaptureHandoff(BaseModel):
    """Secret-free evidence describing a locally stored backup that a human authorized."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    capture_id: str = Field(min_length=1, max_length=160)
    site_id: str = Field(min_length=1, max_length=160)
    target_address: str = Field(min_length=1, max_length=255)
    target_facts_hash: str = Field(min_length=64, max_length=64)
    scope_hash: str = Field(min_length=64, max_length=64)
    backup_reference: str = Field(min_length=1, max_length=240)
    backup_sha256: str = Field(min_length=64, max_length=64)
    capture_state: str = Field(pattern="^(verified|not_verifiable)$")
    evidence_ids: tuple[str, ...] = ()
    human_capture_authorization_reference: str = Field(min_length=1, max_length=200)
    automatic_capture_permitted: bool = False
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detail: str = Field(min_length=1, max_length=500)


class AgentBackupCaptureHandoff:
    """Store an already-authorized local capture and emit evidence without device access or secrets."""

    def __init__(self, backup_manager: BackupManager) -> None:
        """Bind the handoff to the agent's local redacting backup store."""

        self._backup_manager = backup_manager

    def record_local_capture(
        self,
        *,
        capture_id: str,
        scope: AuthorizedScope,
        discovery: DiscoveryResult,
        backup_payload: bytes | str,
        storage_path: str | Path,
        human_capture_authorization_reference: str,
        evidence_ids: Iterable[str] = (),
    ) -> BackupCaptureHandoff:
        """Record a human-authorized local capture after scope and observed-identity validation."""

        if not human_capture_authorization_reference.startswith("approval://"):
            raise ValueError("human_capture_authorization_reference must use the approval:// scheme")
        if discovery.state is not DiscoveryState.DISCOVERED or discovery.facts is None:
            raise ValueError("A backup handoff requires a discovered target with observed device facts")
        if not scope.authorizes(discovery.target):
            raise ValueError("The authorized scope does not permit this local backup target")
        facts_hash = self._target_facts_hash(discovery)
        artifact = self._backup_manager.create(
            backup_id=capture_id,
            target_id=discovery.target.address,
            payload=backup_payload,
            storage_path=storage_path,
            backup_reference=f"backup://{capture_id}",
            evidence_ids=evidence_ids,
            source_reference=human_capture_authorization_reference,
        )
        verification = self._backup_manager.verify(capture_id)
        state = "verified" if verification.verified else "not_verifiable"
        detail = (
            "Human-authorized local backup capture is digest-verified and ready for external evidence handoff."
            if verification.verified
            else "Human-authorized local backup capture was recorded but the local digest could not be verified."
        )
        return BackupCaptureHandoff(
            capture_id=capture_id,
            site_id=scope.site_id,
            target_address=discovery.target.address,
            target_facts_hash=facts_hash,
            scope_hash=scope.evidence_hash(),
            backup_reference=artifact.backup_reference,
            backup_sha256=artifact.sha256,
            capture_state=state,
            evidence_ids=artifact.evidence_ids,
            human_capture_authorization_reference=human_capture_authorization_reference,
            automatic_capture_permitted=False,
            detail=detail,
        )

    @staticmethod
    def _target_facts_hash(discovery: DiscoveryResult) -> str:
        """Produce a stable hash for observed identity data without serializing credential references."""

        if discovery.facts is None:
            raise ValueError("Observed device facts are required")
        payload = json.dumps(
            {
                "address": discovery.target.address,
                "protocol": discovery.target.protocol.value,
                "facts": discovery.facts.model_dump(mode="json"),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
