"""Heuristic and predictive RF planning."""
from .rf_model import RFModel
class PredictivePlanner:
    """Produce guarded AP estimates by planning mode."""
    def plan(self, model:RFModel, coverage_area_m2:float|None=None, clients:int|None=None)->dict[str,object]:
        """Return a plan and never claim survey validation without survey evidence."""
        if model.planning_mode not in {"heuristic","predictive","survey_backed"}: raise ValueError("invalid planning mode")
        if coverage_area_m2 is None or clients is None: return {"status":"pending_survey","aps":None,"evidence_basis":model.planning_mode}
        density_factor=1.0 if clients<25 else 1.5 if clients<75 else 2.0
        aps=max(1,round(coverage_area_m2/150*density_factor)); status="survey_validated" if model.planning_mode=="survey_backed" and model.evidence_ids else model.planning_mode
        return {"status":status,"aps":aps,"evidence_basis":model.evidence_ids or [model.planning_mode]}
