from .common import Verifier
from .proof_status import ProofStatus
class RouteSafetyChecker(Verifier):
    """Formal/static verification engine."""
    def verify(self,r):
        routes=r.get("routes");
        if routes is None:return self.result(ProofStatus.NOT_VERIFIABLE,[],["route table unavailable"])
        unsafe=[x for x in routes if x.get("next_hop")==x.get("prefix") or x.get("untrusted",False)];return self.result(ProofStatus.FAILED if unsafe else ProofStatus.VERIFIED,["route next hops are valid"] if not unsafe else [],unsafe,evidence=["route_safety_analysis"])
