"""As-built package generation from supplied project state snapshots."""
from __future__ import annotations
from pathlib import Path
import uuid
from typing import Any, Mapping, Sequence
from ._common import file_sha256, manifest, metadata, safe_json, write_json, write_text
from .diagram_generator import DiagramGenerator
from .report_models import AsBuiltFile, AsBuiltPackage, ReportLanguage

class AsBuiltGenerator:
    """Generate a redacted, hash-manifested as-built package."""
    def __init__(self, diagram_generator: DiagramGenerator | None = None) -> None:
        """Initialize the as-built generator."""
        self.diagram_generator = diagram_generator or DiagramGenerator()
    def generate(self, *, project_snapshot: Mapping[str, Any], design_snapshot: Mapping[str, Any], deployment_snapshot: Mapping[str, Any], operational_snapshot: Mapping[str, Any], evidence_index: Sequence[Mapping[str, Any]] = (), output_directory: str | Path, language: ReportLanguage | str = ReportLanguage.BOTH, sot_basis: Mapping[str, str] | None = None, evidence_basis: Sequence[str] = ()) -> AsBuiltPackage:
        """Write redacted snapshots, evidence index, topology diagram, README, and manifest."""
        root = Path(output_directory); root.mkdir(parents=True, exist_ok=True)
        package_id = f"as-built:{uuid.uuid4()}"
        documents = {"project_snapshot.json": project_snapshot, "design_state.json": design_snapshot, "deployment_state.json": deployment_snapshot, "operational_state.json": operational_snapshot, "evidence_index.json": list(evidence_index)}
        for filename, payload in documents.items(): write_json(root / filename, payload)
        topology = design_snapshot.get("topology") if isinstance(design_snapshot, Mapping) else None
        if isinstance(topology, Mapping) and isinstance(topology.get("nodes"), Sequence) and isinstance(topology.get("links"), Sequence):
            self.diagram_generator.generate(title="As-Built Topology", nodes=topology["nodes"], links=topology["links"], output_path=root / "topology.mmd", language=language, sot_basis=sot_basis, evidence_basis=evidence_basis)
        title = "As-Built Package / حزمة الحالة المنفذة"
        readme = f"# {title}\\n\\n- Package ID: `{package_id}`\\n- Generated at: `{metadata(title=title, language=language, sot_basis=sot_basis, evidence_basis=evidence_basis).generated_at.isoformat()}`\\n- SoT basis: `{dict(sot_basis or {}) or {'status': 'not supplied'}}`\\n- Evidence basis: `{list(evidence_basis) or ['none supplied']}`\\n- Redaction: `applied`\\n- Raw secret values: `not included`\\n\\n## Scope\\n\\nThis package reflects supplied design, deployment, and operational records. Missing records are not treated as evidence of absence. Human acceptance and operational verification remain required.\\n"
        write_text(root / "README.md", readme)
        files = manifest(root, source_domain="as_built")
        write_json(root / "manifest.json", files)
        files = manifest(root, source_domain="as_built")
        return AsBuiltPackage(package_id=package_id, output_directory=str(root), sot_basis=dict(sot_basis or {}), evidence_basis=list(dict.fromkeys(str(item) for item in evidence_basis)), files=[AsBuiltFile(**item) for item in files], redaction_applied=True, secret_values_included=False, limitations=["As-built output is record-based and does not prove undocumented field state.", "Human acceptance and operational verification are required before treating the package as final."])
