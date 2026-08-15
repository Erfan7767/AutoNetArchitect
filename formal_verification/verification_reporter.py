from .proof_status import ProofStatus
class VerificationReporter:
    """Build deployment-consumable verification reports."""
    def report(self,results,intent=None):
        statuses=[x.get("proof_status") for x in results];failed=ProofStatus.FAILED.value in statuses;unverified=[];verified=[];assumptions=[];evidence=[]
        for x in results:verified.extend(x.get("verified_claims",[]));unverified.extend(x.get("unverified_claims",[]));assumptions.extend(x.get("assumptions_affecting_proof",[]));evidence.extend(x.get("evidence_basis",[]))
        status=ProofStatus.FAILED.value if failed else ProofStatus.VERIFIED.value if statuses and all(s==ProofStatus.VERIFIED.value for s in statuses) else ProofStatus.PARTIALLY_VERIFIED.value
        return {"proof_status":status,"production_safe":status==ProofStatus.VERIFIED.value,"verified_claims":verified,"unverified_claims":unverified,"assumptions_affecting_proof":assumptions,"sot_basis":getattr(intent,"source_of_truth","requirements_document") if intent else "requirements_document","evidence_basis":evidence,"deployment_gate":"allow" if status==ProofStatus.VERIFIED.value else "block_or_review","simulation_evidence_separate":True}
