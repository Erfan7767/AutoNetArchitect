from expert_override.rationale_registry import EngineeringRationale, RationaleRegistry

def test_rationale_registry_retains_human_basis():
    registry = RationaleRegistry()
    record = registry.register(EngineeringRationale(rationale_id="rat-1", override_id="ov-1", author_id="eng", author_role="engineer", statement="site survey changes access path", technical_basis=("survey-1",), evidence_ids=("ev-1",)))
    assert registry.get("rat-1") == record and registry.for_override("ov-1") == (record,)

def test_rationale_registry_rejects_duplicate_id():
    registry = RationaleRegistry()
    record = EngineeringRationale(rationale_id="rat-2", override_id="ov-2", author_id="eng", author_role="engineer", statement="reason")
    registry.register(record)
    try:
        registry.register(record)
    except ValueError:
        return
    raise AssertionError("duplicate rationale was accepted")
