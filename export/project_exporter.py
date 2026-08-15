"""Secret-safe project JSON and ZIP exporter."""
from __future__ import annotations
from pathlib import Path
import tempfile
import uuid
from typing import Any, Mapping
from zipfile import ZIP_DEFLATED, ZipFile
from reports._common import manifest, safe_json, write_json, write_text
from .export_models import ExportResult

class ProjectExporter:
    """Export project records with recursive redaction and SoT metadata."""
    def export_json(self, *, project: Mapping[str, Any], output_path: str | Path, sot_basis: Mapping[str, str] | None = None) -> ExportResult:
        """Write a sanitized project JSON export."""
        target = Path(output_path); target.parent.mkdir(parents=True, exist_ok=True)
        payload = {"export_id": f"export:{uuid.uuid4()}", "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "sot_basis": dict(sot_basis or {}), "redaction_applied": True, "secret_values_included": False, "project": dict(project)}
        write_json(target, payload)
        return ExportResult(export_id=str(payload["export_id"]), output_path=str(target), format="json", sot_basis=dict(sot_basis or {}), files=[target.name])
    def export_zip(self, *, project: Mapping[str, Any], output_path: str | Path, sot_basis: Mapping[str, str] | None = None) -> ExportResult:
        """Write a sanitized project ZIP export."""
        target = Path(output_path); target.parent.mkdir(parents=True, exist_ok=True)
        export_id = f"export:{uuid.uuid4()}"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); write_json(root / "project.json", {"export_id": export_id, "sot_basis": dict(sot_basis or {}), "redaction_applied": True, "secret_values_included": False, "project": dict(project)})
            write_text(root / "README.md", "# AutoNetArchitect Project Export\\n\\nRaw secret values are not included. Review SoT basis and scope before reuse.\\n")
            write_json(root / "manifest.json", manifest(root, source_domain="project_export"))
            with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
                for path in sorted(item for item in root.rglob("*") if item.is_file()): archive.write(path, arcname=path.relative_to(root))
        return ExportResult(export_id=export_id, output_path=str(target), format="zip", sot_basis=dict(sot_basis or {}), files=["project.json", "README.md", "manifest.json"])
