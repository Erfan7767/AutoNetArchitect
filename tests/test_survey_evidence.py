"""Wireless RF test."""
from wireless_rf.survey_evidence import SurveyEvidence
def test_survey_validation():
    assert SurveyEvidence("x","s","active_survey","lab",True).usable_for_production()
