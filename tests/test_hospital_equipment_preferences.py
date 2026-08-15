from domain_packs.hospital_clinical.equipment_preferences import HospitalEquipmentPreferences

def test_equipment_preferences_imports_and_scope():
    result = HospitalEquipmentPreferences().design({"sector": "hospital_clinical"})
    assert result["scope_guard"]["applicable"] is True
