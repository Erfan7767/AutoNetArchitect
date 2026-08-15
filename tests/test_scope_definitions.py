from compliance.compliance_models import ComplianceFramework
from compliance.scope_definitions import controls_for, default_scope

def test_scope_is_technical_only_and_disclaims_certification():
    scope = default_scope(ComplianceFramework.HIPAA)
    assert scope.technical_only is True
    assert scope.certification_claim is False
    assert "certification" in scope.disclaimer.lower()

def test_controls_have_required_evidence_domains():
    controls = controls_for(ComplianceFramework.PCI_DSS)
    assert controls
    assert all(control.required_evidence_domains for control in controls)
