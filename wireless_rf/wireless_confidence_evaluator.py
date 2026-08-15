"""Wireless design confidence and production suitability."""
from .rf_model import RFModel
class WirelessConfidenceEvaluator:
    """Downgrade confidence for missing RF inputs and absent survey evidence."""
    def evaluate(self,model:RFModel)->dict[str,object]:
        """Return score, evidence basis, missing inputs, and suitability."""
        missing=model.missing_inputs(); score=1.0-0.12*len(missing); survey=bool(model.evidence_ids) and model.planning_mode=="survey_backed"
        if not survey:score=min(score,.65)
        return {"confidence_score":max(0.0,round(score,2)),"evidence_basis":"survey_backed" if survey else model.planning_mode,"missing_inputs":missing,"production_suitability":"production_suitable" if survey and not missing else "pending_survey_or_inputs","rf_validated":survey and not missing}
