from domain_packs.university_campus.equipment_preferences import UniversityEquipmentPreferences

def test_equipment_preferences_imports_and_scope():
    result = UniversityEquipmentPreferences().design({"sector": "university_campus"})
    assert result["scope_guard"]["applicable"] is True
