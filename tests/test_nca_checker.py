from compliance.nca_checker import NCAComplianceChecker
from compliance.compliance_models import ComplianceFramework

def test_nca_checker_blocks_authoritative_conclusion_without_edition():
    result = NCAComplianceChecker().assess()
    assert result.framework == ComplianceFramework.NCA
    assert result.overall_state.value == "not_verifiable_with_current_inputs"
    assert result.scope.authoritative_obligations_supplied is False

def test_nca_checker_accepts_explicit_edition_but_remains_technical_only():
    result = NCAComplianceChecker().assess(framework_version="human-supplied-edition", authoritative_obligations_supplied=True)
    assert result.scope.framework_version == "human-supplied-edition"
    assert result.scope.certification_claim is False
