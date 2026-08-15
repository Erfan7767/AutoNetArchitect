"""Wireless RF test."""
from wireless_rf.rf_model import RFModel
from wireless_rf.wireless_confidence_evaluator import WirelessConfidenceEvaluator
def test_pending_without_survey():
    result=WirelessConfidenceEvaluator().evaluate(RFModel("heuristic")); assert result["production_suitability"]=="pending_survey_or_inputs" and not result["rf_validated"]
