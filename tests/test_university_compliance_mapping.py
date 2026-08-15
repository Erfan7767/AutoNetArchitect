from domain_packs.university_campus.compliance_mapping import UniversityComplianceMapping

def test_compliance_mapping_imports_and_scope():
    result = UniversityComplianceMapping().design({"sector": "university_campus"})
    assert result["scope_guard"]["applicable"] is True
