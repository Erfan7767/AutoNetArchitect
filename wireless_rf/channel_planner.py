"""Channel planning with regional constraints."""
from .spectrum_constraints import SpectrumConstraints
class ChannelPlanner:
    """Select channels only from the regional allowed set."""
    def __init__(self,constraints: SpectrumConstraints|None=None)->None:self.constraints=constraints or SpectrumConstraints()
    def plan(self,region:str,band:str,access_points:int)->dict[str,object]:
        """Return a channel plan or an explicit blocked state."""
        channels=self.constraints.channels(region,band)
        if not channels:return {"status":"blocked_unknown_region_or_band","channels":[]}
        return {"status":"planned","channels":[channels[i%len(channels)] for i in range(access_points)]}
