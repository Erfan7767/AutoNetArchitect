from compliance.cis_benchmark_checker import CISBenchmarkComplianceChecker
from compliance.compliance_models import ComplianceFramework

def test_cis_checker_includes_hardening_control():
    result = CISBenchmarkComplianceChecker().assess()
    assert result.framework == ComplianceFramework.CIS_BENCHMARK
    assert any("HARDEN" in item.control.control_id for item in result.controls)

def test_cis_checker_requires_exact_benchmark_scope_for_authority():
    result = CISBenchmarkComplianceChecker().assess()
    assert result.scope.authoritative_obligations_supplied is False
    assert result.deployment_gate == "blocked_pending_review"
