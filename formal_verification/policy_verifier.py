from .common import Verifier
from .proof_status import ProofStatus
class PolicyVerifier(Verifier):
    """Formal/static verification engine."""
    def verify(self,r):
        policies=r.get("policies");
        if policies is None:return self.result(ProofStatus.NOT_VERIFIABLE,[],["policy set unavailable"],source_of_truth=r.get("source_of_truth","requirements_document"))
        conflicts=[p for p in policies if p.get("action")=="deny" and p.get("precedence") is None];status=ProofStatus.FAILED if conflicts else ProofStatus.VERIFIED;return self.result(status,[] if conflicts else ["policy set has explicit precedence"],conflicts,source_of_truth=r.get("source_of_truth","requirements_document"),evidence=["formal_policy_analysis"])
