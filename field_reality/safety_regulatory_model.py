"""Safety and regulatory site controls."""
from __future__ import annotations
from dataclasses import dataclass, field
@dataclass
class SafetyRegulatoryModel:
    """Safety and regulatory site controls."""
    site_id: str
    regulatory_context: str = "unknown"
    safety_induction_required: bool | None = None
    permit_status: str = "unknown"
    compliance_approval: bool | None = None
