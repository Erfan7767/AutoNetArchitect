from .common import Verifier
from .proof_status import ProofStatus
class LoopRiskAnalyzer(Verifier):
    """Formal/static verification engine."""
    def verify(self,r):
        edges=r.get("edges");
        if edges is None:return self.result(ProofStatus.NOT_VERIFIABLE,[],["topology edges unavailable"])
        graph={};
        for a,b in edges:graph.setdefault(a,[]).append(b)
        visiting=set();visited=set();cycles=[]
        def dfs(n,path):
            if n in visiting:cycles.append(path+[n]);return
            if n in visited:return
            visiting.add(n)
            for nxt in graph.get(n,[]):dfs(nxt,path+[n])
            visiting.remove(n);visited.add(n)
        for n in graph:dfs(n,[])
        return self.result(ProofStatus.FAILED if cycles else ProofStatus.VERIFIED,["no directed routing cycles"] if not cycles else [],cycles,evidence=["graph_cycle_analysis"])
