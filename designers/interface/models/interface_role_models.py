from dataclasses import dataclass
@dataclass
class InterfaceRoleAssignment:
    """Role assigned to an interface."""
    interface_name:str
    role:str
    rationale:str
