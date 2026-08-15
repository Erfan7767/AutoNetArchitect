from equipment.capability_matrix import CapabilityMatrix, CapabilityRecord
from equipment.equipment_selector import EquipmentSelector
from equipment.licensing_db import LicenseRecord, LicensingDB


def test_selector_returns_traceable_rationale_and_confidence():
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
    selector = EquipmentSelector([{"equipment_id": "acmenet-x1", "vendor": "AcmeNet", "platform": "switch", "model": "X1", "version": "1.5", "production_eligible": True, "vendor_status": "supported"}], matrix, licensing)
    result = selector.select({"required_capabilities": ["routing"], "license_id": "advanced"})
    assert result["status"] == "selected"
    assert result["selected"]["equipment"]["equipment_id"] == "acmenet-x1"
    assert result["confidence"] > 0.9
    assert result["selected"]["evidence_ids"]
    assert result["decision_record"].rationale


def test_unsupported_vendor_cannot_be_auto_selected_for_production():
    selector = EquipmentSelector([{"equipment_id": "unsupported-1", "vendor": "UnknownVendor", "platform": "switch", "model": "U1", "version": "1.0", "production_eligible": False, "vendor_status": "unsupported"}])
    result = selector.select({"required_capabilities": ["routing"], "license_id": "advanced"})
    assert result["status"] == "no_decision"
