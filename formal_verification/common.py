from .proof_status import ProofStatus,EvidenceType
class Verifier:
    """Shared proof result helper; simulation never becomes formal proof."""
    def result(self,status,claims,unverified=None,assumptions=None,source_of_truth="requirements_document",evidence=None):
        return {"proof_status":status.value if hasattr(status,"value") else status,"verified_claims":claims,"unverified_claims":unverified or [],"assumptions_affecting_proof":assumptions or [],"sot_basis":source_of_truth,"evidence_basis":evidence or [],"simulation_evidence_separate":True}
