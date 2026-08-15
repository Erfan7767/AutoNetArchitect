"""Pydantic v2 contracts for the complete documentation generator set."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(str, Enum):
    """Supported engineering document types."""

    HLD = "hld"
    LLD = "lld"
    IP_ADDRESS_PLAN = "ip_address_plan"
    VLAN_DATABASE = "vlan_database"
    PORT_MAPPING = "port_mapping"
    CABLE_SCHEDULE = "cable_schedule"
    ROUTING_DESIGN = "routing_design"
    FIREWALL_RULE_MATRIX = "firewall_rule_matrix"
    ACL_DOCUMENTATION = "acl_documentation"
    NAT_DOCUMENTATION = "nat_documentation"
    WIRELESS_DESIGN = "wireless_design"
    QOS_DESIGN = "qos_design"
    SECURITY_DESIGN = "security_design"
    WAN_DESIGN = "wan_design"
    VPN_DESIGN = "vpn_design"
    DR_PLAN = "dr_plan"
    PHYSICAL_LAYOUT = "physical_layout"
    EQUIPMENT_INVENTORY = "equipment_inventory"
    BOM = "bom"
    SOW = "sow"
    ATP = "atp"
    AS_BUILT = "as_built"
    HANDOVER_PACK = "handover_pack"
    OPERATIONAL_RUNBOOK = "operational_runbook"
    TROUBLESHOOTING_GUIDE = "troubleshooting_guide"
    CHANGE_PROCEDURE = "change_procedure"
    COMPLIANCE_REPORT = "compliance_report"
    NETWORK_INVENTORY = "network_inventory"
    DECISION_LOG = "decision_log"
    ASSUMPTION_REGISTER = "assumption_register"
    RISK_REGISTER = "risk_register"
    VOICE_DESIGN = "voice_design"
    NAC_DESIGN = "nac_design"
    CAPACITY_REPORT = "capacity_report"


class ContentType(str, Enum):
    """Section content representation."""

    TEXT = "text"
    TABLE = "table"
    DIAGRAM = "diagram"
    LIST = "list"
    MIXED = "mixed"


class SectionStatus(str, Enum):
    """Section completion state."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    PENDING = "pending"
    NOT_APPLICABLE = "not_applicable"


class OutputFormat(str, Enum):
    """Supported output formats."""

    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


class RedactionLevel(str, Enum):
    """Documentation redaction policy."""

    NONE = "none"
    STANDARD = "standard"
    STRICT = "strict"


class Language(str, Enum):
    """Documentation language mode."""

    ARABIC = "ar"
    ENGLISH = "en"
    BILINGUAL = "bilingual"


class DocumentSection(BaseModel):
    """Standard section definition for one document."""

    model_config = ConfigDict(extra="forbid")

    section_id: str
    section_title_en: str
    section_title_ar: str
    section_level: int = Field(ge=1, le=3)
    content_type: ContentType
    data_source: str
    mandatory: bool = True
    status: SectionStatus = SectionStatus.PENDING
    pending_reason: str | None = None
    order: int = Field(default=0, ge=0)

    def model_post_init(self, __context: Any) -> None:
        """Require a reason whenever a section is not complete."""
        if self.status == SectionStatus.PENDING and not self.pending_reason:
            object.__setattr__(self, "pending_reason", f"data source unavailable: {self.data_source}")


class ResolvedSectionData(BaseModel):
    """Resolved data and status for one documentation section."""

    model_config = ConfigDict(extra="forbid")

    section: DocumentSection
    content: Any = None
    has_content: bool = False
    status: SectionStatus
    pending_reason: str | None = None
    source_artifacts: list[str] = Field(default_factory=list)
    source_timestamps: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ResolvedData(BaseModel):
    """All section data resolved from source artifacts."""

    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType
    sections: list[ResolvedSectionData] = Field(default_factory=list)
    completeness_score: float = Field(default=0.0, ge=0, le=100)
    mandatory_sections_complete: bool = False
    pending_sections: list[str] = Field(default_factory=list)
    stale_sections: list[str] = Field(default_factory=list)
    sot_basis: dict[str, str] = Field(default_factory=dict)
    evidence_basis: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class CompletenessResult(BaseModel):
    """Completeness assessment before rendering."""

    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType
    completeness_score: float = Field(ge=0, le=100)
    mandatory_sections_complete: bool
    pending_sections: list[str] = Field(default_factory=list)
    stale_sections: list[str] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    can_render: bool = True


class GeneratedDocument(BaseModel):
    """Final generated documentation artifact."""

    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType
    file_path: str
    generation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sot_basis: dict[str, str] = Field(default_factory=dict)
    schema_version: str = "1.0"
    completeness_score: float = Field(ge=0, le=100)
    pending_sections: list[str] = Field(default_factory=list)
    redacted: bool = True
    language: Language
    output_format: OutputFormat
    page_count: int | None = Field(default=None, ge=0)
    assumptions: list[str] = Field(default_factory=list)
    evidence_basis: list[str] = Field(default_factory=list)
    disclaimer: str = "Generated from supplied source artifacts only. PENDING sections identify missing or incomplete source data."

    def model_post_init(self, __context: Any) -> None:
        """Enforce mandatory safety metadata."""
        if not self.sot_basis:
            object.__setattr__(self, "sot_basis", {"status": "not supplied"})
        if not self.redacted and self.output_format != OutputFormat.JSON:
            raise ValueError("non-redacted rendered documentation requires explicit internal JSON-only policy")


class DocumentRequest(BaseModel):
    """Orchestration request for one document."""

    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType
    project_id: str
    output_format: OutputFormat
    language: Language = Language.BILINGUAL
    redaction_level: RedactionLevel = RedactionLevel.STANDARD
    sections_override: list[str] | None = None
    output_path: str
    schema_version: str = "1.0"
    minimum_completeness: float = Field(default=0.0, ge=0, le=100)
    allow_pending: bool = True
