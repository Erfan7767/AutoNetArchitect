"""Secret-safe Mermaid diagram generation."""
from __future__ import annotations
from pathlib import Path
import re
from typing import Mapping, Sequence
from ._common import metadata, write_text
from .report_models import ReportArtifact, ReportLanguage

class DiagramGenerator:
    """Generate editable Mermaid topology diagrams from supplied nodes and links."""
    def generate(self, *, title: str, nodes: Sequence[Mapping[str, str]], links: Sequence[Mapping[str, str]], output_path: str | Path, language: ReportLanguage | str = ReportLanguage.BOTH, sot_basis: Mapping[str, str] | None = None, evidence_basis: Sequence[str] = ()) -> ReportArtifact:
        """Write a sanitized Mermaid flowchart."""
        selected = ReportLanguage(language)
        meta = metadata(title=title, language=selected, sot_basis=sot_basis, evidence_basis=evidence_basis)
        target = Path(output_path); target.parent.mkdir(parents=True, exist_ok=True)
        lines = ["%% AutoNetArchitect diagram", f"%% report_id: {meta.report_id}", f"%% generated_at: {meta.generated_at.isoformat()}", f"%% sot_basis: {meta.sot_basis}", "flowchart LR"]
        ids = {}
        for index, node in enumerate(nodes):
            raw_id = str(node.get("id", f"node_{index}")); safe_id = re.sub(r"[^A-Za-z0-9_]", "_", raw_id) or f"node_{index}"; ids[raw_id] = safe_id
            label = str(node.get("label", raw_id)).replace("[", "(").replace("]", ")").replace('"', "'")
            lines.append(f'    {safe_id}["{label}"]')
        for link in links:
            source = ids.get(str(link.get("source", "")), re.sub(r"[^A-Za-z0-9_]", "_", str(link.get("source", "unknown"))))
            target_id = ids.get(str(link.get("target", "")), re.sub(r"[^A-Za-z0-9_]", "_", str(link.get("target", "unknown"))))
            label = str(link.get("label", "")).replace("|", "/").replace('"', "'")
            lines.append(f'    {source} -->|{label}| {target_id}')
        write_text(target, "\\n".join(lines) + "\\n")
        return ReportArtifact(metadata=meta, output_path=str(target), format="mmd")
