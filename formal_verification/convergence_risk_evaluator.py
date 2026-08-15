from .common import Verifier
from .proof_status import ProofStatus
class ConvergenceRiskEvaluator(Verifier):
    """Formal/static verification engine."""
    def verify(self,r):
        inputs=["failure_domains","timers","routing_protocols"];missing=[x for x in inputs if not r.get(x)];risk=[]
        if r.get("timer_mismatch"):risk.append("timer mismatch")
        if r.get("single_path"):risk.append("single path")
        status=ProofStatus.NOT_VERIFIABLE if missing else ProofStatus.FAILED if risk else ProofStatus.PARTIALLY_VERIFIED;return self.result(status,[] if risk else ["no configured convergence risk detected"],missing+risk,evidence=["convergence_static_analysis"])
