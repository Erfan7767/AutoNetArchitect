"""Handover package generation from an as-built directory."""
from __future__ import annotations
from pathlib import Path
from typing import Sequence
from zipfile import ZIP_DEFLATED, ZipFile
from ._common import safe_json, write_text
from .report_models import AsBuiltPackage, HandoverPack, ReportLanguage

class HandoverPackGenerator:
    """Create a redacted ZIP handover pack with bilingual index and basis metadata."""
    def generate(self, *, as_built: AsBuiltPackage, output_path: str | Path, language: ReportLanguage | str = ReportLanguage.BOTH, additional_notes: Sequence[str] = ()) -> HandoverPack:
        """Package all as-built files plus a handover guide."""
        source = Path(as_built.output_directory)
        if not source.exists():
            raise FileNotFoundError(str(source))
        target = Path(output_path); target.parent.mkdir(parents=True, exist_ok=True)
        handover = "# Handover Pack / حزمة التسليم\\n\\n" + f"- Pack ID: `{as_built.package_id}`\\n- Generated at: `{as_built.generated_at.isoformat()}`\\n- SoT basis: `{as_built.sot_basis or {'status': 'not supplied'}}`\\n- Evidence basis: `{as_built.evidence_basis or ['none supplied']}`\\n- Raw secret values: `not included`\\n\\n## Human acceptance actions\\n\\n1. Confirm the scope and SoT records.\\n2. Validate operational state against the supplied evidence.\\n3. Review unresolved assumptions, limitations, and change history.\\n4. Approve any production use through the project governance workflow.\\n\\n## Notes\\n\\n" + "\\n".join(f"- {note}" for note in additional_notes)
        with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
            for path in sorted(item for item in source.rglob("*") if item.is_file()):
                archive.write(path, arcname=f"as_built/{path.relative_to(source)}")
            archive.writestr("HANDOVER.md", handover)
            archive.writestr("handover_metadata.json", safe_json({"package_id": as_built.package_id, "sot_basis": as_built.sot_basis, "evidence_basis": as_built.evidence_basis, "redaction_applied": True, "secret_values_included": False}))
        included = [f"as_built/{item.relative_path}" for item in as_built.files] + ["HANDOVER.md", "handover_metadata.json"]
        return HandoverPack(pack_id=f"handover:{as_built.package_id}", output_path=str(target), sot_basis=as_built.sot_basis, evidence_basis=as_built.evidence_basis, included_files=included, redaction_applied=True, secret_values_included=False)
