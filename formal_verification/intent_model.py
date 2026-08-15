from dataclasses import dataclass,field
@dataclass
class IntentModel:
    """Traceable business/security/connectivity/compliance/resilience intent."""
    business:dict=field(default_factory=dict)
    security:dict=field(default_factory=dict)
    connectivity:dict=field(default_factory=dict)
    compliance:dict=field(default_factory=dict)
    resilience:dict=field(default_factory=dict)
    source_of_truth:str="requirements_document"
    evidence_ids:list[str]=field(default_factory=list)
    def claims(self):
        """Return all intent claims as traceable records."""
        return {"business":self.business,"security":self.security,"connectivity":self.connectivity,"compliance":self.compliance,"resilience":self.resilience}
