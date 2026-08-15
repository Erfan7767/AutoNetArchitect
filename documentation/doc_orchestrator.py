"""Orchestration for complete source-driven documentation generation."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from .doc_completeness_checker import DocCompletenessChecker
from .doc_data_resolver import DocDataResolver
from .doc_models import DocumentRequest, DocumentType, GeneratedDocument, Language, OutputFormat, RedactionLevel
from .doc_redaction_engine import DocRedactionEngine
from .doc_section_registry import DocumentSectionRegistry
from .generators import (
    ACLDocumentationGenerator, AsBuiltGenerator, ATPGenerator, AssumptionRegisterGenerator, BOMDocumentGenerator, CableScheduleGenerator, CapacityReportGenerator, ChangeProcedureGenerator, ComplianceReportGenerator, DecisionLogGenerator, DRPlanGenerator, EquipmentInventoryGenerator, FirewallRuleMatrixGenerator, HandoverPackGenerator, HLDGenerator, IPAddressPlanGenerator, LLDGenerator, NACDesignGenerator, NATDocumentationGenerator, NetworkInventoryGenerator, OperationalRunbookGenerator, PhysicalLayoutGenerator, PortMappingGenerator, QoSDesignGenerator, RiskRegisterGenerator, RoutingDesignGenerator, SecurityDesignGenerator, SOWGenerator, TroubleshootingGuideGenerator, VLANDatabaseGenerator, VPNDesignGenerator, VoiceDesignGenerator, WANDesignGenerator, WirelessDesignGenerator,
)
from .generators.base_generator import BaseDocumentGenerator
from .renderers import ExcelRenderer, HTMLRenderer, JSONRenderer, MarkdownRenderer, PDFRenderer, WordRenderer


class DocumentOrchestrator:
    """Coordinate source resolution, quality gates, redaction, and rendering."""

    def __init__(self, *, registry: DocumentSectionRegistry | None = None, resolver: DocDataResolver | None = None, checker: DocCompletenessChecker | None = None, redactor: DocRedactionEngine | None = None) -> None:
        """Initialize the documentation pipeline with replaceable governance components."""
        self.registry = registry or DocumentSectionRegistry()
        self.resolver = resolver or DocDataResolver()
        self.checker = checker or DocCompletenessChecker()
        self.redactor = redactor or DocRedactionEngine()
        self.generators: dict[DocumentType, BaseDocumentGenerator] = {
            generator.document_type: generator for generator in [
                HLDGenerator(), LLDGenerator(), IPAddressPlanGenerator(), VLANDatabaseGenerator(), PortMappingGenerator(), CableScheduleGenerator(), RoutingDesignGenerator(), FirewallRuleMatrixGenerator(), ACLDocumentationGenerator(), NATDocumentationGenerator(), WirelessDesignGenerator(), QoSDesignGenerator(), SecurityDesignGenerator(), WANDesignGenerator(), VPNDesignGenerator(), DRPlanGenerator(), PhysicalLayoutGenerator(), EquipmentInventoryGenerator(), BOMDocumentGenerator(), SOWGenerator(), ATPGenerator(), AsBuiltGenerator(), HandoverPackGenerator(), OperationalRunbookGenerator(), TroubleshootingGuideGenerator(), ChangeProcedureGenerator(), ComplianceReportGenerator(), NetworkInventoryGenerator(), DecisionLogGenerator(), AssumptionRegisterGenerator(), RiskRegisterGenerator(), VoiceDesignGenerator(), NACDesignGenerator(), CapacityReportGenerator(),
            ]
        }
        self.renderers = {OutputFormat.PDF: PDFRenderer(), OutputFormat.WORD: WordRenderer(), OutputFormat.EXCEL: ExcelRenderer(), OutputFormat.MARKDOWN: MarkdownRenderer(), OutputFormat.HTML: HTMLRenderer(), OutputFormat.JSON: JSONRenderer()}

    def generate(self, request: DocumentRequest, artifacts: Mapping[str, Any]) -> GeneratedDocument:
        """Generate one document or raise a transparent quality-gate error."""
        resolved = self.resolver.resolve(document_type=request.document_type, artifacts=artifacts, registry=self.registry, sections_override=request.sections_override)
        completeness = self.checker.check(resolved, minimum_score=request.minimum_completeness, allow_pending=request.allow_pending)
        if not completeness.can_render:
            raise ValueError("documentation generation blocked: " + "; ".join(completeness.blocking_reasons))
        generator = self.generators[request.document_type]
        content = generator.generate(resolved, language=request.language)
        redacted_content, findings, applied = self.redactor.redact(content, request.redaction_level)
        redacted_content["redaction_findings"] = findings
        Path(request.output_path).parent.mkdir(parents=True, exist_ok=True)
        renderer = self.renderers[request.output_format]
        page_count = renderer.render(redacted_content, request.output_path, watermark="CONFIDENTIAL" if request.redaction_level != RedactionLevel.NONE else "NONE")
        sot_basis = resolved.sot_basis or {"status": "not supplied"}
        redacted = applied or request.redaction_level != RedactionLevel.NONE
        return GeneratedDocument(document_type=request.document_type, file_path=request.output_path, sot_basis=sot_basis, schema_version=request.schema_version, completeness_score=completeness.completeness_score, pending_sections=completeness.pending_sections, redacted=redacted, language=Language(request.language), output_format=OutputFormat(request.output_format), page_count=page_count, assumptions=resolved.assumptions, evidence_basis=resolved.evidence_basis)

    def generate_many(self, requests: Sequence[DocumentRequest], artifacts: Mapping[str, Any]) -> list[GeneratedDocument]:
        """Generate a sequence in order, stopping on the first blocked artifact."""
        return [self.generate(request, artifacts) for request in requests]
