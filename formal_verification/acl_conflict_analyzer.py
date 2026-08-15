from .common import Verifier
from .proof_status import ProofStatus
class ACLConflictAnalyzer(Verifier):
    """Formal/static verification engine."""
    def verify(self,r):
        rules=r.get("acl_rules");
        if rules is None:return self.result(ProofStatus.NOT_VERIFIABLE,[],["ACL rules unavailable"])
        shadowed=[];conflicts=[]
        for i,rule in enumerate(rules):
            for prior in rules[:i]:
                if rule.get("match")==prior.get("match") and prior.get("action")!=rule.get("action"):conflicts.append(rule)
                if rule.get("match")==prior.get("match"):shadowed.append(rule)
        status=ProofStatus.FAILED if conflicts else ProofStatus.PARTIALLY_VERIFIED if shadowed else ProofStatus.VERIFIED;return self.result(status,["no contradictory ACL rules"] if not conflicts else [],shadowed+conflicts,evidence=["acl_static_analysis"])
