from enum import Enum
class Dot1XMode(str,Enum):
    MONITOR="monitor"; LOW_IMPACT="low_impact"; CLOSED="closed"
class IdentityType(str,Enum):
    EMPLOYEE="employee"; CONTRACTOR="contractor"; GUEST="guest"; DEVICE="device"; UNKNOWN="unknown"
