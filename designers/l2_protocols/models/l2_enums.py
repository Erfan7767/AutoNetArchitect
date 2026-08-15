from enum import Enum
class STPMode(str,Enum):
    PVST="pvst_plus"; RAPID_PVST="rapid_pvst_plus"; MSTP="mstp"
class PortRole(str,Enum):
    ACCESS="access"; TRUNK="trunk"; UPLINK="uplink"; SERVER="server"
