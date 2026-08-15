"""Contracts for secret-safe project and configuration exports."""
from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field

class ExportResult(BaseModel):
    """Export descriptor with redaction and basis metadata."""
    model_config = ConfigDict(extra="forbid")
    export_id: str
    output_path: str
    format: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sot_basis: dict[str, str] = Field(default_factory=dict)
    files: list[str] = Field(default_factory=list)
    redaction_applied: bool = True
    secret_values_included: bool = False
    disclaimer: str = "Export contains sanitized supplied records only; raw secret values are never included."
    def model_post_init(self, __context: object) -> None:
        """Reject unsafe export descriptors."""
        if self.secret_values_included:
            raise ValueError("raw secret values cannot be included in exports")
