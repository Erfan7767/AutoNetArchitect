from enum import Enum
class VoiceStrategy(str,Enum):
    ON_PREM="on_prem"; CLOUD="cloud"; HYBRID="hybrid"
