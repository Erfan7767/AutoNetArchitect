"""Traceable bill-of-materials generation for network designs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from designers.base_designer import BaseDesigner


@dataclass(frozen=True)
class BOMItem:
    """One BOM line with explicit selection and evidence state."""

    category: str
    identifier: str
    description: str
    quantity: int | float
    unit: str
    selection_state: str
    evidence_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class BOMGenerator(BaseDesigner):
    """Build a BOM without inventing missing SKUs, dimensions, rates, or quantities."""

    REQUIRED_CATEGORIES = ("devices", "optics", "PSUs", "support_contracts", "installation_labor", "racks", "cables", "spares")

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name or self.__class__.__name__)

    @staticmethod
    def _quantity(item: dict[str, Any]) -> int | float:
        value = item.get("quantity")
        return value if isinstance(value, (int, float)) and value >= 0 else 0

    @staticmethod
    def _as_items(value: Any) -> list[dict[str, Any]]:
        return [dict(item) for item in value] if isinstance(value, list) else []

    def _pending(self, category: str, identifier: str, description: str, missing_input: str) -> BOMItem:
        self.record_assumption(f"bom_missing_{category}", missing_input, f"The {category} line is retained as pending human input rather than receiving an invented SKU or quantity.")
        return BOMItem(category, identifier, description, 0, "unit", "pending_human_input", metadata={"missing_input": missing_input})

    def generate(self, design: dict[str, Any]) -> dict[str, Any]:
        """Generate all required BOM categories and expose blocked inputs."""
        items: list[BOMItem] = []
        devices = self._as_items(design.get("devices"))
        if devices:
            for device in devices:
                quantity = self._quantity(device)
                identifier = str(device.get("equipment_id", device.get("model", "device_without_identifier")))
                state = "selected" if quantity > 0 and device.get("evidence_ids") else "pending_human_input"
                if state != "selected":
                    self.record_assumption(f"device_{identifier}_evidence_or_quantity", "unresolved", "Device BOM inclusion requires a quantity and capability evidence IDs.")
                items.append(BOMItem("devices", identifier, str(device.get("description", identifier)), quantity, "unit", state, tuple(str(value) for value in device.get("evidence_ids", [])), tuple(str(value) for value in device.get("source_ids", [])), {"vendor": device.get("vendor"), "model": device.get("model")}))
                psu_count = device.get("psu_count")
                if psu_count is None and device.get("power_redundancy") == "dual":
                    psu_count = 2
                if isinstance(psu_count, (int, float)) and psu_count >= 0 and quantity > 0:
                    items.append(BOMItem("PSUs", f"psu_for:{identifier}", f"Power supplies for {identifier}", quantity * psu_count, "unit", "derived_from_human_device_input", tuple(str(value) for value in device.get("evidence_ids", [])), (), {"per_device_quantity": psu_count}))
                else:
                    items.append(self._pending("PSUs", f"psu_for:{identifier}", f"Power supplies for {identifier}", f"psu_count_for_{identifier}"))
                contract = device.get("support_contract")
                if isinstance(contract, dict) and contract.get("contract_id") and quantity > 0:
                    items.append(BOMItem("support_contracts", str(contract["contract_id"]), f"Support contract for {identifier}", quantity, "contract", "human_selected_or_evidenced", tuple(str(value) for value in contract.get("evidence_ids", [])), tuple(str(value) for value in contract.get("source_ids", [])), {"term": contract.get("term"), "scope": contract.get("scope")}))
                else:
                    items.append(self._pending("support_contracts", f"support_for:{identifier}", f"Support contract for {identifier}", f"support_contract_for_{identifier}"))
                for optic in self._as_items(device.get("optics")):
                    optic_id = str(optic.get("optic_id", optic.get("part_number", "optic_without_identifier")))
                    optic_state = "selected_with_evidence" if optic.get("evidence_ids") and quantity > 0 else "pending_human_input"
                    items.append(BOMItem("optics", optic_id, str(optic.get("description", optic_id)), self._quantity(optic) * quantity, "unit", optic_state, tuple(str(value) for value in optic.get("evidence_ids", [])), tuple(str(value) for value in optic.get("source_ids", [])), {"compatible_device": identifier}))
        else:
            items.append(self._pending("devices", "devices_pending", "Network devices", "device_schedule"))
            items.append(self._pending("PSUs", "psus_pending", "Power supplies", "device_power_schedule"))
            items.append(self._pending("support_contracts", "support_contracts_pending", "Support contracts", "support_contract_scope"))
        if not any(item.category == "optics" for item in items):
            optics = self._as_items(design.get("optics"))
            if optics:
                for optic in optics:
                    optic_id = str(optic.get("optic_id", optic.get("part_number", "optic_without_identifier")))
                    state = "selected_with_evidence" if optic.get("evidence_ids") else "pending_human_input"
                    items.append(BOMItem("optics", optic_id, str(optic.get("description", optic_id)), self._quantity(optic), "unit", state, tuple(str(value) for value in optic.get("evidence_ids", [])), tuple(str(value) for value in optic.get("source_ids", [])), {}))
            else:
                items.append(self._pending("optics", "optics_pending", "Optics and transceivers", "optic_schedule_and_compatibility_evidence"))
        for category, description, key in (("racks", "Racks and cabinets", "racks"), ("cables", "Structured and patch cabling", "cables"), ("spares", "Recommended spares", "spares")):
            supplied = self._as_items(design.get(key))
            if supplied:
                for entry in supplied:
                    identifier = str(entry.get("identifier", entry.get("part_number", entry.get("cable_type", f"{category}_item"))))
                    items.append(BOMItem(category, identifier, str(entry.get("description", identifier)), self._quantity(entry), str(entry.get("unit", "unit")), "human_supplied_schedule", tuple(str(value) for value in entry.get("evidence_ids", [])), tuple(str(value) for value in entry.get("source_ids", [])), {"dimensions": entry.get("dimensions"), "length": entry.get("length")}))
            else:
                items.append(self._pending(category, f"{category}_pending", description, f"{key}_schedule"))
        labor = design.get("installation_labor")
        if isinstance(labor, dict) and isinstance(labor.get("hours"), (int, float)) and labor.get("hours") >= 0:
            items.append(BOMItem("installation_labor", str(labor.get("identifier", "installation_labor")), "Installation labor estimate", labor["hours"], "hour", "estimate_from_supplied_rate_or_hours", tuple(str(value) for value in labor.get("evidence_ids", [])), tuple(str(value) for value in labor.get("source_ids", [])), {"hourly_rate": labor.get("hourly_rate"), "rate_currency": labor.get("rate_currency"), "estimate_basis": labor.get("estimate_basis")}))
        else:
            items.append(self._pending("installation_labor", "installation_labor_pending", "Installation labor estimate", "labor_hours_and_rate_or_basis"))
        grouped = {category: [item for item in items if item.category == category] for category in self.REQUIRED_CATEGORIES}
        pending = [item.identifier for item in items if item.selection_state == "pending_human_input"]
        status = "complete" if not pending else "blocked_pending_bom_inputs"
        decision = self.record_decision("bom_composition", status, "Included every required BOM category and retained missing commercial or field inputs as explicit pending lines.", alternatives=["partial_bom_without_pending_lines"], rejection_reasons={"partial_bom_without_pending_lines": "would hide unknown quantities, SKUs, or site-dependent requirements"})
        return {"status": status, "items": items, "by_category": grouped, "pending_inputs": pending, "decision_record": decision, "assumptions": list(self.assumptions)}

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        """BaseDesigner entry point for BOM generation."""
        return self.generate(requirements)
