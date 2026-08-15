from learning_memory.discrepancy_registry import ActualOutcome, DiscrepancyRecord, DiscrepancyRegistry, DiscrepancySeverity, DiscrepancyType, HumanCorrection

def _record(identifier="d-1"):
    return DiscrepancyRecord(discrepancy_id=identifier, discrepancy_type=DiscrepancyType.DESIGN_MISMATCH, severity=DiscrepancySeverity.HIGH, scenario_id="scenario-1", decision_id="decision-1", proposed_value="choice-a", evidence_state="partially_verified", evidence_ids=("ev-1",), actual_outcome=ActualOutcome(status="failed", summary="field path unavailable", source="deployment", evidence_ids=("obs-1",)))

def test_registry_records_links_and_closes_discrepancy():
    registry = DiscrepancyRegistry()
    registry.record(_record())
    corrected = registry.attach_correction("d-1", HumanCorrection(correction_id="c-1", actor_id="eng-1", actor_role="engineer", action="replace_path", corrected_value="choice-b", rationale="survey found a pathway constraint", evidence_ids=("survey-1",)))
    closed = registry.close("d-1", closure_reference="change://C-1", evidence_ids=("verify-1",))
    assert corrected.human_correction is not None and closed.status == "closed" and closed.closed_at is not None

def test_registry_filters_by_type_and_scenario():
    registry = DiscrepancyRegistry()
    registry.record(_record())
    assert registry.by_scenario("scenario-1") and registry.by_type(DiscrepancyType.DESIGN_MISMATCH)
