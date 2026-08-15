from domain_packs.hospital_clinical.guest_staff_patient_access import GuestStaffPatientAccess

def test_guest_staff_patient_access_imports_and_scope():
    result = GuestStaffPatientAccess().design({"sector": "hospital_clinical"})
    assert result["scope_guard"]["applicable"] is True
