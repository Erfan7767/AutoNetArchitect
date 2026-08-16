"""Secret-free local inventory review summaries for the Windows shell."""

from __future__ import annotations

from collections import Counter
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from site_agent.models import DiscoveryResult, DiscoveryState


class InventoryDisposition(str, Enum):
    """Human-review disposition derived directly from discovery state."""

    EVIDENCE_RECORDED = "evidence_recorded"
    ABSTAINED = "abstained"
    UNREACHABLE = "unreachable"
    UNAUTHORIZED = "unauthorized"


class InventoryReviewRow(BaseModel):
    """One display-safe inventory row with no credentials or raw command output."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    address: str = Field(min_length=1, max_length=255)
    protocol: str = Field(min_length=1, max_length=40)
    state: DiscoveryState
    disposition: InventoryDisposition
    vendor: str | None = None
    platform: str | None = None
    software_version: str | None = None
    evidence_message: str = Field(min_length=1, max_length=500)
    requires_human_review: bool


class InventoryReviewSummary(BaseModel):
    """Aggregate review state; it never converts unresolved rows into supported devices."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rows: tuple[InventoryReviewRow, ...]
    state_counts: dict[str, int]
    unresolved_count: int
    abstained_count: int
    all_targets_reviewed: bool


def summarize_inventory(results: list[DiscoveryResult]) -> InventoryReviewSummary:
    """Build a review summary from read-only results without adding inferred facts."""

    rows: list[InventoryReviewRow] = []
    for result in results:
        if result.state is DiscoveryState.DISCOVERED and result.facts is not None:
            disposition = InventoryDisposition.EVIDENCE_RECORDED
            requires_human_review = False
            vendor = result.facts.vendor
            platform = result.facts.platform
            software_version = result.facts.software_version
        elif result.state is DiscoveryState.UNAUTHORIZED:
            disposition = InventoryDisposition.UNAUTHORIZED
            requires_human_review = True
            vendor = platform = software_version = None
        elif result.state is DiscoveryState.UNREACHABLE:
            disposition = InventoryDisposition.UNREACHABLE
            requires_human_review = True
            vendor = platform = software_version = None
        else:
            disposition = InventoryDisposition.ABSTAINED
            requires_human_review = True
            vendor = platform = software_version = None
        rows.append(
            InventoryReviewRow(
                address=result.target.address,
                protocol=result.target.protocol.value,
                state=result.state,
                disposition=disposition,
                vendor=vendor,
                platform=platform,
                software_version=software_version,
                evidence_message=result.message,
                requires_human_review=requires_human_review,
            )
        )
    counts = Counter(result.state.value for result in results)
    unresolved_count = sum(1 for row in rows if row.requires_human_review)
    abstained_count = sum(1 for row in rows if row.disposition is InventoryDisposition.ABSTAINED)
    return InventoryReviewSummary(
        rows=tuple(rows),
        state_counts=dict(counts),
        unresolved_count=unresolved_count,
        abstained_count=abstained_count,
        all_targets_reviewed=bool(rows) and unresolved_count == 0,
    )
