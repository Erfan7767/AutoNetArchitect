"""Orchestration for source-driven network diagram generation."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from documentation.doc_redaction_engine import DocRedactionEngine

from .diagram_models import DiagramModel, DiagramRequest, DiagramStyle, DiagramType, GeneratedDiagram, OutputFormat, RedactionLevel
from .diagram_style_manager import DiagramStyleManager
from .generators import (
    CablePathwayGenerator,
    DRTopologyGenerator,
    DependencyGraphGenerator,
    FloorPlanGenerator,
    L2TopologyGenerator,
    L3TopologyGenerator,
    LogicalTopologyGenerator,
    PhysicalTopologyGenerator,
    RackElevationGenerator,
    RoutingDomainGenerator,
    SecurityZoneGenerator,
    SiteOverviewGenerator,
    VLANMapGenerator,
    VPNTopologyGenerator,
    WANTopologyGenerator,
    WirelessCoverageGenerator,
)
from .generators.ip_schema_generator import IPSchemaGenerator
from .exporters import DrawioExporter, GraphvizExporter, MermaidExporter, PDFExporter, PNGExporter, SVGExporter
from .icon_library import IconLibrary
from .label_engine import LabelEngine
from .layout_engine import LayoutEngine
from .legend_generator import LegendGenerator


class DiagramOrchestrator:
    """Generate, quality-label, redact, layout, and export diagram artifacts."""

    def __init__(self, *, redactor: DocRedactionEngine | None = None) -> None:
        """Initialize all supported generators and exporters."""
        self.icon_library = IconLibrary()
        self.style_manager = DiagramStyleManager()
        self.layout_engine = LayoutEngine()
        self.label_engine = LabelEngine()
        self.legend_generator = LegendGenerator()
        self.redactor = redactor or DocRedactionEngine()
        self.generators = {
            DiagramType.PHYSICAL_TOPOLOGY: PhysicalTopologyGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.LOGICAL_TOPOLOGY: LogicalTopologyGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.L3_TOPOLOGY: L3TopologyGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.L2_TOPOLOGY: L2TopologyGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.SECURITY_ZONES: SecurityZoneGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.WAN_TOPOLOGY: WANTopologyGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.SITE_OVERVIEW: SiteOverviewGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.RACK_ELEVATION: RackElevationGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.FLOOR_PLAN: FloorPlanGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.CABLE_PATHWAY: CablePathwayGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.VLAN_MAP: VLANMapGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.ROUTING_DOMAIN: RoutingDomainGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.VPN_TOPOLOGY: VPNTopologyGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.DR_TOPOLOGY: DRTopologyGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.WIRELESS_COVERAGE: WirelessCoverageGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.IP_SCHEMA: IPSchemaGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
            DiagramType.DEPENDENCY_GRAPH: DependencyGraphGenerator(icon_library=self.icon_library, style_manager=self.style_manager),
        }
        self.exporters = {
            OutputFormat.PNG: PNGExporter(),
            OutputFormat.SVG: SVGExporter(),
            OutputFormat.PDF: PDFExporter(),
            OutputFormat.DRAWIO: DrawioExporter(),
            OutputFormat.MERMAID: MermaidExporter(),
            OutputFormat.GRAPHVIZ: GraphvizExporter(),
        }

    def generate(self, request: DiagramRequest, artifacts: Mapping[str, Any]) -> GeneratedDiagram:
        """Generate one diagram from supplied artifacts and export it."""
        generator = self.generators[request.diagram_type]
        model = generator.generate(artifacts=artifacts, scope=request.scope, scope_value=request.scope_value, detail_level=request.detail_level.value)
        model = self._apply_style(model, request.style)
        model = self.layout_engine.layout(model)
        model = self.label_engine.apply_labels(model, request.labels)
        legend = self.legend_generator.generate(model)
        model = model.model_copy(update={"legend": legend})
        redacted_value, findings, applied = self.redactor.redact(model.model_dump(mode="json"), self._documentation_redaction(request.redaction_level))
        redacted_model = DiagramModel.model_validate(redacted_value)
        if findings:
            redacted_model = redacted_model.model_copy(update={"warnings": list(dict.fromkeys(redacted_model.warnings + findings))})
        Path(request.output_path).parent.mkdir(parents=True, exist_ok=True)
        page_count = self.exporters[request.output_format].export(redacted_model, request.output_path)
        uncertain = [node.node_id for node in redacted_model.nodes if node.uncertain] + [edge.edge_id for edge in redacted_model.edges if edge.uncertain]
        source_artifacts = sorted({source for node in redacted_model.nodes for source in node.source_artifacts} | {source for edge in redacted_model.edges for source in edge.source_artifacts})
        return GeneratedDiagram(diagram_type=request.diagram_type, project_id=request.project_id, scope=request.scope, detail_level=request.detail_level, output_format=request.output_format, file_path=request.output_path, sot_basis=request.sot_basis or {"status": "not supplied"}, evidence_basis=request.evidence_basis, schema_version=request.schema_version, redaction_level=request.redaction_level, redacted=applied or request.redaction_level != RedactionLevel.NONE, node_count=len(redacted_model.nodes), edge_count=len(redacted_model.edges), group_count=len(redacted_model.groups), page_count=page_count, uncertain_elements=uncertain, warnings=redacted_model.warnings, source_artifacts=source_artifacts)

    def generate_many(self, requests: Sequence[DiagramRequest], artifacts: Mapping[str, Any]) -> list[GeneratedDiagram]:
        """Generate diagrams in request order."""
        return [self.generate(request, artifacts) for request in requests]

    def model(self, request: DiagramRequest, artifacts: Mapping[str, Any]) -> DiagramModel:
        """Return the prepared model without writing a file for preview or testing."""
        generator = self.generators[request.diagram_type]
        prepared = generator.generate(artifacts=artifacts, scope=request.scope, scope_value=request.scope_value, detail_level=request.detail_level.value)
        prepared = self._apply_style(prepared, request.style)
        prepared = self.layout_engine.layout(prepared)
        prepared = self.label_engine.apply_labels(prepared, request.labels)
        return prepared.model_copy(update={"legend": self.legend_generator.generate(prepared)})

    def documentation_artifact(self, model: DiagramModel) -> dict[str, Any]:
        """Return a structure consumable by documentation generators."""
        return {"diagram_type": model.diagram_type.value, "title": model.title, "nodes": [node.model_dump(mode="json") for node in model.nodes], "edges": [edge.model_dump(mode="json") for edge in model.edges], "groups": [group.model_dump(mode="json") for group in model.groups], "legend": [entry.model_dump(mode="json") for entry in model.legend], "warnings": model.warnings, "page_count": model.page_count}

    def _apply_style(self, model: DiagramModel, selected: DiagramStyle | str) -> DiagramModel:
        """Apply style colors without changing source topology."""
        config = self.style_manager.style(selected)
        nodes = [node.model_copy(update={"style_overrides": {**node.style_overrides, "fill": node.style_overrides.get("fill", self.style_manager.node_color(node.node_type, selected))}}) for node in model.nodes]
        edges = [edge.model_copy(update={"color": self.style_manager.edge_color(edge.edge_type.value, selected)}) for edge in model.edges]
        return model.model_copy(update={"nodes": nodes, "edges": edges, "metadata": {**model.metadata, "style": DiagramStyle(selected).value, "background": config.get("background", "#FFFFFF")}})

    @staticmethod
    def _documentation_redaction(level: RedactionLevel) -> Any:
        """Map diagram redaction enum to the documentation redaction enum by value."""
        from documentation.doc_models import RedactionLevel as DocumentationRedactionLevel
        return DocumentationRedactionLevel(level.value)
