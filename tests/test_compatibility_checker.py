from equipment.capability_matrix import CapabilityMatrix, CapabilityRecord
from equipment.compatibility_checker import CompatibilityChecker
from equipment.licensing_db import LicenseRecord, LicensingDB


def build_checker():
    matrix = CapabilityMatrix(
        [CapabilityRecord("AcmeNet", "switch", "X1", "routing", "1.0", "2.0", ("advanced",), "supported_with_license", ("ev-routing",), confidence=0.94)],
        {"ev-routing": {"source_id": "src", "verification_state": "verified", "revoked": False, "expired": False}},
        {"src": {"verified": True}},
    )
    licensing = LicensingDB(
        [LicenseRecord("AcmeNet", "advanced", "Advanced", ("routing",), True, "verified", ("ev-license",), confidence=0.92)],
        {"ev-license": {"source_id": "src-license", "verification_state": "verified", "revoked": False, "expired": False}},
        {"src-license": {"verified": True}},
    )
    return CompatibilityChecker(matrix, licensing)


def test_compatible_candidate_passes_all_evidence_checks():
    report = build_checker().check({"vendor": "AcmeNet", "platform": "switch", "model": "X1", "version": "1.5", "production_eligible": True, "vendor_status": "supported"}, {"required_capabilities": ["routing"], "license_id": "advanced"})
    assert report.compatible is True
    assert report.confidence > 0.9


def test_production_candidate_without_vendor_approval_is_blocked():
    report = build_checker().check({"vendor": "AcmeNet", "platform": "switch", "model": "X1", "version": "1.5", "production_eligible": False, "vendor_status": "catalogued_not_production_approved"}, {"required_capabilities": ["routing"], "license_id": "advanced"})
    assert report.compatible is False
    assert "vendor_or_equipment_not_production_approved" in report.reasons
