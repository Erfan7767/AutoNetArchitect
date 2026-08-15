"""Fault domain modeling."""
from dataclasses import dataclass
@dataclass(frozen=True)
class FaultDomain:
    """Failure isolation domain."""
    domain_id:str
    members:list[str]
    failure_scope:str
