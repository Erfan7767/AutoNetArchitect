from compliance.hipaa_checker import HIPAAComplianceChecker
from compliance.compliance_models import ComplianceFramework

def test_hipaa_checker_uses_hipaa_framework_and_technical_scope():
    result = HIPAAComplianceChecker().assess()
    assert result.framework == ComplianceFramework.HIPAA
    assert result.scope.technical_only is True
    assert result.scope.readiness_claim is False
