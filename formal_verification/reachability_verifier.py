from .common import Verifier
from .proof_status import ProofStatus
class ReachabilityVerifier(Verifier):
    """Formal/static verification engine."""
    def verify(self,r):
        allowed=r.get("allowed_reachability",[]);denied=r.get("denied_reachability",[]);paths=r.get("paths");
        if paths is None:return self.result(ProofStatus.NOT_VERIFIABLE,[],["forwarding paths unavailable"],source_of_truth=r.get("source_of_truth","requirements_document"),evidence=["simulation" if r.get("simulation_run") else "none"])
        violations=[x for x in denied if x in paths];missing=[x for x in allowed if x not in paths];status=ProofStatus.FAILED if violations else ProofStatus.PARTIALLY_VERIFIED if missing else ProofStatus.VERIFIED;return self.result(status,[x for x in allowed if x in paths],violations+missing,source_of_truth=r.get("source_of_truth","requirements_document"),evidence=["formal_path_check"])
