from enum import Enum
class FHRPProtocol(str,Enum):
    HSRP="hsrp"; VRRP="vrrp"; GLBP="glbp"
