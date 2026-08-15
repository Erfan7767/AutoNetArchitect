"""Certificate renewal planning and controlled execution."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .cert_inventory import CertInventory, CertificateRecord
from .pki_manager import PKIManager


@dataclass(frozen=True)
class RenewalTask:
    """Auditable renewal task."""

    cert_id: str
    status: str
    due_at: str
    reason: str
    requires_approval: bool = True


class RenewalScheduler:
    """Plan certificate renewals and execute only through an explicit callback/approval."""

    def __init__(self, inventory: CertInventory, pki_manager: PKIManager) -> None:
        self.inventory = inventory
        self.pki_manager = pki_manager

    def plan(self, within_days: int = 30, now: datetime | None = None) -> tuple[RenewalTask, ...]:
        """Create tasks for due-soon and expired active certificates."""
        now = now or datetime.now(timezone.utc)
        tasks: list[RenewalTask] = []
        for record in self.inventory.list(include_revoked=False):
            status = self.inventory.status(record.cert_id, now)
            if status in {"due_soon", "expired"}:
                tasks.append(RenewalTask(record.cert_id, status, record.not_after, "certificate requires renewal before continued use" if status == "due_soon" else "certificate has expired", True))
        return tuple(tasks)

    def execute(self, tasks: tuple[RenewalTask, ...], approve: Callable[[RenewalTask], bool], validity_days: int | None = None) -> tuple[CertificateRecord, ...]:
        """Renew approved tasks and leave rejected tasks untouched."""
        renewed: list[CertificateRecord] = []
        for task in tasks:
            if not approve(task):
                continue
            renewed.append(self.pki_manager.renew(task.cert_id, validity_days))
        return tuple(renewed)
