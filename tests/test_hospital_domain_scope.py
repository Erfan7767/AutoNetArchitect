from domain_packs.hospital_clinical.domain_scope import HospitalClinicalNetworksPack

def test_hospital_scope_is_explicit_and_exclusive():
    assert HospitalClinicalNetworksPack().design({"sector": "hospital_clinical"})["scope_guard"]["applicable"] is True
    assert HospitalClinicalNetworksPack().design({"sector": "banking"})["scope_guard"]["status"] == "out_of_scope"
