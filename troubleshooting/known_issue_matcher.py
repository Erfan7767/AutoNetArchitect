"""Known issue matching with explicit version and symptom scope."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field

from .models import SymptomClassification


class KnownIssueMatch(BaseModel):
    """A bounded match to a known issue record."""

    model_config = ConfigDict(extra="forbid")

    issue_id: str
    vendor: str = ""
    platform: str = ""
    affected_versions: list[str] = Field(default_factory=list)
    symptom_patterns: list[str] = Field(default_factory=list)
    root_cause: str = ""
    workaround: str = ""
    fix_version: str = ""
    reference: str = ""
    confidence: float
    evidence_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class KnownIssueMatcher:
    """Match known issues only when supplied records have explicit scope."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def match(self, classification: SymptomClassification, records: Iterable[Mapping[str, Any]], *, vendor: str = "", platform: str = "", version: str = "") -> list[KnownIssueMatch]:
        """Return matches based on explicit symptom, vendor, platform, and version signals."""
        results: list[KnownIssueMatch] = []
        for raw in records:
            item = dict(raw)
            record_vendor = str(item.get("vendor", ""))
            record_platform = str(item.get("platform", ""))
            versions = [str(value) for value in item.get("affected_versions", [])]
            patterns = [str(value).lower() for value in item.get("symptom_patterns", [])]
            vendor_match = not vendor or not record_vendor or vendor.lower() == record_vendor.lower()
            platform_match = not platform or not record_platform or platform.lower() == record_platform.lower()
            version_match = not version or not versions or version in versions
            symptom_match = any(pattern in classification.subtype.lower() or pattern in classification.primary_class.value.lower() or pattern in " ".join(classification.matched_terms).lower() for pattern in patterns)
            if vendor_match and platform_match and version_match and symptom_match:
                score = 0.45 + (0.15 if record_vendor and vendor_match else 0.0) + (0.15 if record_platform and platform_match else 0.0) + (0.15 if version and version_match else 0.0) + 0.1
                results.append(KnownIssueMatch(issue_id=str(item.get("issue_id", "unknown-issue")), vendor=record_vendor, platform=record_platform, affected_versions=versions, symptom_patterns=patterns, root_cause=str(item.get("root_cause", "")), workaround=str(item.get("workaround", "")), fix_version=str(item.get("fix_version", "")), reference=str(item.get("reference", "")), confidence=min(score, 0.95), evidence_ids=[str(value) for value in item.get("evidence_ids", [])], limitations=["known issue match is advisory and does not prove the active root cause"]))
        if not records:
            self.assumptions.append(Assumption("known_issue_database", "not_supplied", "known issue matching cannot be inferred without records", True))
        self.decisions.append(DecisionRecord("KnownIssueMatcher", "known-issue-match", "scoped_pattern_matching", "require symptom pattern plus compatible product scope", ["scoped_pattern_matching", "free_text_similarity_only"], {"scoped_pattern_matching": "selected", "free_text_similarity_only": "rejected without product scope"}))
        return sorted(results, key=lambda item: item.confidence, reverse=True)
