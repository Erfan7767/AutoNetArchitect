from .common import Verifier
from .proof_status import ProofStatus
class BlastRadiusEstimator(Verifier):
    """Formal/static verification engine."""
    def verify(self,r):
        graph=r.get("dependency_graph");failure=r.get("failure_node");
        if graph is None or failure is None:return self.result(ProofStatus.NOT_VERIFIABLE,[],["dependency graph or failure node unavailable"])
        affected=set();stack=[failure]
        while stack:
            n=stack.pop()
            if n in affected:continue
            affected.add(n);stack.extend(graph.get(n,[]))
        return {"proof_status":ProofStatus.PARTIALLY_VERIFIED.value,"affected_nodes":sorted(affected),"blast_radius_count":len(affected),"verified_claims":["dependency closure computed"],"unverified_claims":["real-world failure behavior"],"assumptions_affecting_proof":[],"sot_basis":r.get("source_of_truth","topology_document"),"evidence_basis":["dependency_graph_analysis"],"simulation_evidence_separate":True}
