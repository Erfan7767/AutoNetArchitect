from dataclasses import dataclass,field
@dataclass
class GuestModel:
    """NAC model."""
    vlan:int|None=None
    portal_required:bool=True
    workflow:str="self_registration"
