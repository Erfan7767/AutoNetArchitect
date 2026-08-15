from enum import Enum
class MPLSService(str,Enum):
    L3VPN="l3vpn"; L2VPN="l2vpn"; BOTH="both"
class MPLSScope(str,Enum):
    CE="ce_side"; INTERNAL="internal_limited"; SP="sp_out_of_scope"
