from domain_packs.hospital_clinical.compliance_mapping import HospitalComplianceMapping

def test_compliance_mapping_imports_and_scope():
    result = HospitalComplianceMapping().design({"sector": "hospital_clinical"})
    assert result["scope_guard"]["applicable"] is True
