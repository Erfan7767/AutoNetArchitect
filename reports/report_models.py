"""Pydantic v2 contracts shared by reports and as-built exports."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReportLanguage(str, Enum):
    """Supported report language modes."""

    ENGLISH = "en"
    ARABIC = "ar"
    BOTH = "both"


class ReportMetadata(BaseModel):
    """Mandatory metadata embedded in every generated artifact."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    title: str
    language: ReportLanguage
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sot_basis: dict[str, str] = Field(default_factory=dict)
    evidence_basis: list[str] = Field(default_factory=list)
    redaction_applied: bool = True
    secret_values_included: bool = False
    disclaimer: str = "Generated from supplied project records only; absence of a record is not evidence that the underlying state exists."

    def model_post_init(self, __context: Any) -> None:
        """Enforce secret-safe metadata claims."""
        if self.secret_values_included:
            raise ValueError("report artifacts cannot include raw secret values")
        if not self.disclaimer.strip():
            raise ValueError("report disclaimer is mandatory")


class ReportArtifact(BaseModel):
    """Generated report descriptor."""

    model_config = ConfigDict(extra="forbid")

    metadata: ReportMetadata
    output_path: str
    format: str
    redaction_findings: list[str] = Field(default_factory=list)


class AsBuiltFile(BaseModel):
    """One file in an as-built package."""

    model_config = ConfigDict(extra="forbid")

    relative_path: str
    sha256: str
    source_domain: str
    redacted: bool = True


class AsBuiltPackage(BaseModel):
    """Descriptor for a generated as-built package."""

    model_config = ConfigDict(extra="forbid")

    package_id: str
    output_directory: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sot_basis: dict[str, str] = Field(default_factory=dict)
    evidence_basis: list[str] = Field(default_factory=list)
    files: list[AsBuiltFile] = Field(default_factory=list)
    redaction_applied: bool = True
    secret_values_included: bool = False
    limitations: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Prevent unsafe package descriptors."""
        if self.secret_values_included:
            raise ValueError("as-built packages cannot include raw secret values")


class HandoverPack(BaseModel):
    """Descriptor for a generated handover pack."""

    model_config = ConfigDict(extra="forbid")

    pack_id: str
    output_path: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sot_basis: dict[str, str] = Field(default_factory=dict)
    evidence_basis: list[str] = Field(default_factory=list)
    included_files: list[str] = Field(default_factory=list)
    redaction_applied: bool = True
    secret_values_included: bool = False
    disclaimer: str = "Handover documentation is generated from supplied records and does not replace human acceptance, operational validation, or change approval."

    def model_post_init(self, __context: Any) -> None:
        """Enforce handover safety contract."""
        if self.secret_values_included:
            raise ValueError("handover packs cannot include raw secret values")
