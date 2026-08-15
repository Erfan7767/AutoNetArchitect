"""Known interference source registry."""
class InterferenceRegistry:
    """Track measured or unresolved interference profiles."""
    def __init__(self)->None:self.sources=[]
    def add(self,source:str,evidence_id:str|None=None)->None:"""Add an interference source with optional evidence.""";self.sources.append({"source":source,"evidence_id":evidence_id})
    def profile(self)->str:"""Return unknown when no measured profile exists.""";return "unknown" if not self.sources else "documented"
