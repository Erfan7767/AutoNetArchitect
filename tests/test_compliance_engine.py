from compliance.compliance_engine import ComplianceEngine
from compliance.compliance_models import ComplianceFramework, EvidenceDomain, EvidenceReference, ComplianceState
from compliance.scope_definitions import default_scope

def evidence_for(controls):
    result = []
    for control in controls:
        for index, domain in enumerate(control.required_evidence_domains):
            result.append(EvidenceReference(evidence_id=f"{control.control_id}:{index}", domain=domain, source="test-source", source_record_id=f"record:{control.control_id}:{index}", source_version="test-1", control_ids=[control.control_id]))
    return result

def test_engine_maps_complete_evidence_to_partial_without_authoritative_scope():
    from compliance.scope_definitions import controls_for
    controls = controls_for(ComplianceFramework.HIPAA)
    assessment = ComplianceEngine().assess(framework=ComplianceFramework.HIPAA, scope=default_scope(ComplianceFramework.HIPAA, authoritative_obligations_supplied=False), evidence=evidence_for(controls), sot_basis={"DESIGN":"sot:design"})
    assert assessment.overall_state == ComplianceState.PARTIALLY_VERIFIED
    assert assessment.certification_statement.startswith("No certification")

def test_engine_complete_mapping_and_report_declare_sot_and_evidence_basis():
    from compliance.scope_definitions import controls_for
    controls = controls_for(ComplianceFramework.PCI_DSS)
    engine = ComplianceEngine()
    assessment = engine.assess(framework=ComplianceFramework.PCI_DSS, scope=default_scope(ComplianceFramework.PCI_DSS, framework_version="human-supplied-edition", authoritative_obligations_supplied=True), evidence=evidence_for(controls), sot_basis={"DESIGN":"sot:design", "CONFIGURATION":"artifact:config", "OPERATIONAL":"snapshot:operational"})
    report = engine.report(assessment, language="ar")
    assert assessment.overall_state == ComplianceState.VERIFIED
    assert report.sot_basis_declared is True
    assert report.evidence_basis_declared is True
    assert assessment.certification_statement.startswith("No certification")


def test_engine_requires_evidence_for_verified_state():
    assessment = ComplianceEngine().assess(framework=ComplianceFramework.PCI_DSS, scope=default_scope(ComplianceFramework.PCI_DSS, authoritative_obligations_supplied=True), sot_basis={"DESIGN":"sot:design"})
    assert assessment.overall_state == ComplianceState.NOT_VERIFIABLE
    assert assessment.deployment_gate == "blocked_pending_review"

def test_engine_failed_evidence_is_explicit_failure():
    control_id = "hipaa.NET-ACCESS"
    evidence = [EvidenceReference(evidence_id="negative", domain=EvidenceDomain.CONFIGURATION, source="test", control_ids=[control_id], supports=False, notes="control observation failed")]
    assessment = ComplianceEngine().assess(framework=ComplianceFramework.HIPAA, scope=default_scope(ComplianceFramework.HIPAA), evidence=evidence, control_observations={control_id:{"evidence_ids":["negative"]}})
    control = next(item for item in assessment.controls if item.control.control_id == control_id)
    assert control.state == ComplianceState.FAILED
