"""Roaming design constraints."""
class RoamingModel:
    """Assess roaming claims against evidence."""
    def assess(self,fast_roaming:bool,evidence_ids:list[str])->dict[str,object]:
        """Return supported, pending, or not requested."""
        if not fast_roaming:return {"status":"not_requested"}
        return {"status":"evidence_backed" if evidence_ids else "pending_survey","evidence_ids":evidence_ids}
