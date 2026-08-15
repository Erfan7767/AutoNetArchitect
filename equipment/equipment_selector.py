"""Evidence-gated equipment selection with auditable rationale."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from designers.base_designer import BaseDesigner

from .capability_matrix import CapabilityMatrix
from .compatibility_checker import CompatibilityChecker
from .licensing_db import LicensingDB


class EquipmentSelector(BaseDesigner):
    """Select equipment only when requested production capabilities are evidenced."""

    def __init__(self, catalog: list[dict[str, Any]] | None = None, capability_matrix: CapabilityMatrix | None = None, licensing_db: LicensingDB | None = None, compatibility_checker: CompatibilityChecker | None = None, name: str | None = None) -> None:
        super().__init__(name or self.__class__.__name__)
        self.catalog = list(catalog or [])
        self.capability_matrix = capability_matrix or CapabilityMatrix()
        self.licensing_db = licensing_db or LicensingDB()
        self.compatibility_checker = compatibility_checker or CompatibilityChecker(self.capability_matrix, self.licensing_db)

    @classmethod
    def from_json(cls, catalog_path: str | Path, capability_path: str | Path, licensing_path: str | Path, optics_path: str | Path | None = None) -> "EquipmentSelector":
        """Build a selector from governed catalog, capability, license, and optic stores."""
        catalog_payload = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
        capability_matrix = CapabilityMatrix.from_json(capability_path)
        licensing_db = LicensingDB.from_json(licensing_path)
        optics: list[dict[str, Any]] = []
        if optics_path is not None:
            optic_payload = json.loads(Path(optics_path).read_text(encoding="utf-8"))
            optics = list(optic_payload.get("optics", []))
        checker = CompatibilityChecker(capability_matrix, licensing_db, optics)
        return cls(catalog_payload.get("equipment", []), capability_matrix, licensing_db, checker)

    def select(self, requirements: dict[str, Any], production: bool = True) -> dict[str, Any]:
        """Rank candidates and return no-decision when evidence is insufficient."""
        candidates: list[dict[str, Any]] = []
        rejections: dict[str, list[str]] = {}
        vendor_allowlist = {str(value).lower() for value in requirements.get("vendor_allowlist", [])}
        for equipment in self.catalog:
            identifier = str(equipment.get("equipment_id", f"{equipment.get('vendor', 'unknown')}:{equipment.get('model', 'unknown')}"))
            if vendor_allowlist and str(equipment.get("vendor", "")).lower() not in vendor_allowlist:
                rejections[identifier] = ["vendor_not_in_allowlist"]
                continue
            report = self.compatibility_checker.check(equipment, requirements, production=production)
            if report.compatible:
                candidates.append({"equipment": equipment, "confidence": report.confidence, "evidence_ids": list(report.evidence_ids), "compatibility_checks": report.checks})
            else:
                rejections[identifier] = list(report.reasons)
        candidates.sort(key=lambda item: (-float(item["confidence"]), str(item["equipment"].get("equipment_id", ""))))
        selected = candidates[0] if candidates else None
        if selected is None:
            self.record_assumption("equipment_selection_evidence", "unresolved", "No catalog candidate satisfied every production capability, licensing, version, and vendor policy check.")
            decision = self.record_decision("equipment_selection", "no_decision", "Production selection is blocked until a supported candidate has a complete capability and licensing evidence chain.", alternatives=list(rejections), rejection_reasons={key: "; ".join(value) for key, value in rejections.items()})
            return {"status": "no_decision", "selected": None, "alternatives": [], "rejections": rejections, "confidence": 0.0, "rationale": "No evidence-backed equipment candidate is available.", "decision_record": decision, "assumptions": list(self.assumptions)}
        equipment = selected["equipment"]
        decision = self.record_decision("equipment_selection", equipment.get("equipment_id", equipment.get("model")), "Selected the highest-confidence candidate that passed vendor, capability, version, license, and optic evidence checks.", alternatives=[item["equipment"].get("equipment_id", item["equipment"].get("model")) for item in candidates[1:]], rejection_reasons={key: "; ".join(value) for key, value in rejections.items()})
        return {"status": "selected" if production else "preview_selected", "selected": selected, "alternatives": candidates[1:], "rejections": rejections, "confidence": float(selected["confidence"]), "rationale": "Selection is restricted to an evidence-backed candidate and remains traceable to returned evidence IDs.", "decision_record": decision, "assumptions": list(self.assumptions)}

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        """BaseDesigner entry point for production equipment selection."""
        return self.select(requirements, production=True)
