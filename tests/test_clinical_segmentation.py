from domain_packs.hospital_clinical.clinical_segmentation import ClinicalSegmentation

def test_clinical_and_nonclinical_boundaries_exist():
    result = ClinicalSegmentation().design({"sector": "hospital"})["artifact"]
    assert "patient_monitoring" in result["clinical_critical_zones"]
    assert "guest" in result["non_clinical_zones"]
    assert result["clinical_review"]["required"] is True
