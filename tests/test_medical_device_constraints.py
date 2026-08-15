from domain_packs.hospital_clinical.medical_device_constraints import MedicalDeviceConstraints

def test_medical_device_inventory_is_required():
    result = MedicalDeviceConstraints().design({"sector": "hospital"})
    assert result["artifact"]["status"] == "blocked_missing_device_inventory"
    assert result["artifact"]["clinical_review"]["status"] == "human_review_required"
