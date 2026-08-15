from domain_packs.hospital_clinical.acceptance_criteria import HospitalAcceptanceCriteria

def test_hospital_acceptance_requires_human_review():
    result = HospitalAcceptanceCriteria().design({"sector": "hospital"})["artifact"]
    assert result["review_threshold"] == "mandatory_human_review_for_clinically_sensitive_paths"
    assert result["clinical_readiness_claim"] == "not_allowed_without_authoritative_human_approval_and_scope"
