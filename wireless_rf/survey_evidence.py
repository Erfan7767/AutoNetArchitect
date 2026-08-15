"""Survey evidence registry."""
from dataclasses import dataclass
@dataclass(frozen=True)
class SurveyEvidence:
    """Traceable RF survey evidence."""
    evidence_id:str
    site_id:str
    survey_type:str
    source:str
    validated:bool=False
    def usable_for_production(self)->bool:
        """Return whether survey evidence supports production claims."""
        return self.validated and self.survey_type in {"predictive_validation","active_survey","passive_survey"}
class SurveyEvidenceRegistry:
    """Store survey evidence by identifier."""
    def __init__(self)->None:self.records={}
    def add(self,evidence:SurveyEvidence)->None:"""Register survey evidence.""";self.records[evidence.evidence_id]=evidence
    def get(self,evidence_id:str)->SurveyEvidence:return self.records[evidence_id]
