from compliance.iso27001_checker import ISO27001ComplianceChecker
from compliance.compliance_models import ComplianceFramework

def test_iso_checker_does_not_claim_isms_certification():
    result = ISO27001ComplianceChecker().assess(framework_version="2022")
    assert result.framework == ComplianceFramework.ISO_27001
    assert "certification" in result.certification_statement.lower()
    assert result.human_review_required is True
