from dataclasses import dataclass,field
@dataclass
class PortChannelModel:
    """Layer-2 model."""
    channel_id:int
    members:list[str]=field(default_factory=list)
    protocol:str="lacp"
