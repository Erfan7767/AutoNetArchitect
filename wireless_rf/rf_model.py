"""RF planning model with explicit missing inputs."""
from dataclasses import dataclass,field
@dataclass
class RFModel:
    """Represent RF inputs without inventing physical values."""
    planning_mode:str
    floor_dimensions_m2:float|None=None
    materials:dict[str,str]=field(default_factory=dict)
    mounting_height_m:float|None=None
    client_density:float|None=None
    interference_profile:str|None=None
    region:str|None=None
    band:str|None=None
    evidence_ids:list[str]=field(default_factory=list)
    def missing_inputs(self)->list[str]:
        """Return inputs required for higher-confidence RF planning."""
        return [k for k,v in (("floor_dimensions_m2",self.floor_dimensions_m2),("materials",self.materials),("mounting_height_m",self.mounting_height_m),("client_density",self.client_density),("interference_profile",self.interference_profile)) if v in (None,{},"")]
