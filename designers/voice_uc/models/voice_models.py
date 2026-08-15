from dataclasses import dataclass,field
@dataclass
class VoiceNetworkModel:
    """Network support artifact for voice and UC."""
    strategy:str
    endpoints:int=0
    voice_vlans:list[int]=field(default_factory=list)
    metadata:dict=field(default_factory=dict)
