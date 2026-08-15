"""Secret-safe configuration exporter."""
from __future__ import annotations
from pathlib import Path
import re
import tempfile
import uuid
from typing import Any, Mapping
from zipfile import ZIP_DEFLATED, ZipFile
from reports._common import manifest, sanitize, safe_json, write_json, write_text
from .export_models import ExportResult

class ConfigExporter:
    """Export device configuration artifacts without raw secret values."""
    def export_directory(self, *, configurations: Mapping[str, Any], output_directory: str | Path, sot_basis: Mapping[str, str] | None = None) -> ExportResult:
        """Write one sanitized file per device plus metadata and manifest."""
        root = Path(output_directory); root.mkdir(parents=True, exist_ok=True)
        export_id = f"config-export:{uuid.uuid4()}"
        for device_id, config in configurations.items():
            safe_name = "".join(character if character.isalnum() or character in "._-" else "_" for character in str(device_id)) or "device"
            if isinstance(config, str):
                write_text(root / f"{safe_name}.cfg", self._sanitize_config_text(config))
            else:
                write_json(root / f"{safe_name}.json", config)
        write_json(root / "export_metadata.json", {"export_id": export_id, "sot_basis": dict(sot_basis or {}), "redaction_applied": True, "secret_values_included": False})
        entries = manifest(root, source_domain="config_export")
        write_json(root / "manifest.json", entries)
        return ExportResult(export_id=export_id, output_path=str(root), format="directory", sot_basis=dict(sot_basis or {}), files=[item["relative_path"] for item in manifest(root, source_domain="config_export")])
    @staticmethod
    def _sanitize_config_text(config: str) -> str:
        """Redact key-value and whitespace-delimited secret commands safely."""
        sanitized = str(sanitize(config))
        pattern = re.compile(r"(?im)^(\s*(?:password|passwd|secret|token|api[-_]?key|community|psk|shared[-_]?secret)\s+)(?!secret://)([^\s#]+)")
        return pattern.sub(lambda match: match.group(1) + "<REDACTED>", sanitized)

    def export_zip(self, *, configurations: Mapping[str, Any], output_path: str | Path, sot_basis: Mapping[str, str] | None = None) -> ExportResult:
        """Write a sanitized configuration ZIP."""
        target = Path(output_path); target.parent.mkdir(parents=True, exist_ok=True)
        export_id = f"config-export:{uuid.uuid4()}"
        with tempfile.TemporaryDirectory() as directory:
            directory_result = self.export_directory(configurations=configurations, output_directory=directory, sot_basis=sot_basis)
            with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
                root = Path(directory)
                for path in sorted(item for item in root.rglob("*") if item.is_file()): archive.write(path, arcname=path.relative_to(root))
        return ExportResult(export_id=export_id, output_path=str(target), format="zip", sot_basis=dict(sot_basis or {}), files=directory_result.files)
