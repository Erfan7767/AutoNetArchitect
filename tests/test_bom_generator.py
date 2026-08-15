from equipment.bom_generator import BOMGenerator


def test_bom_contains_all_required_categories_when_inputs_are_complete():
    result = BOMGenerator().generate({
        "devices": [{"equipment_id": "acmenet-x1", "quantity": 2, "evidence_ids": ["ev-device"], "psu_count": 2, "support_contract": {"contract_id": "support-x1", "term": "human-selected"}, "optics": [{"optic_id": "optic-10g", "quantity": 4, "evidence_ids": ["ev-optic"]}]}],
        "racks": [{"identifier": "rack-a", "quantity": 1, "dimensions": "human-supplied"}],
        "cables": [{"identifier": "fiber-sm", "quantity": 8, "unit": "run", "length": "human-supplied"}],
        "spares": [{"identifier": "spare-x1", "quantity": 1}],
        "installation_labor": {"hours": 16, "estimate_basis": "human-supplied work package"},
    })
    assert set(result["by_category"]) == {"devices", "optics", "PSUs", "support_contracts", "installation_labor", "racks", "cables", "spares"}
    assert result["status"] == "complete"
    assert result["by_category"]["PSUs"][0].quantity == 4


def test_bom_keeps_missing_inputs_explicitly_pending():
    result = BOMGenerator().generate({})
    assert result["status"] == "blocked_pending_bom_inputs"
    assert "installation_labor_pending" in result["pending_inputs"]
    assert "racks_pending" in result["pending_inputs"]
