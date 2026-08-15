from benchmarking.pilot_evidence_registry import PilotEvidenceRecord, PilotEvidenceRegistry, PilotStatus

def test_pilot_registry_requires_human_validation_for_usable_evidence():
    registry = PilotEvidenceRegistry()
    registry.register(PilotEvidenceRecord(pilot_id="pilot-1", environment_name="lab-1", scope="one branch", scenario_ids=("brownfield-branch",), metric_results=({"metric": "design_acceptance_rate", "rate": 0.8},), evidence_ids=("ev-pilot",), limitations=("short observation window",)))
    assert not registry.usable()
    validated = registry.validate("pilot-1", human_review_reference="review://pilot-1", limitations=("single vendor",))
    assert validated.status == PilotStatus.VALIDATED and registry.usable()
