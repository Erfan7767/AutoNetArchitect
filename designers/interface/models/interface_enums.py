from enum import Enum
class InterfaceStatus(str,Enum):
    AVAILABLE="available"; RESERVED="reserved"; ALLOCATED="allocated"; DISABLED="disabled"
class InterfaceRole(str,Enum):
    UPLINK="uplink_to_core"; ACCESS="downlink_to_endpoint"; MANAGEMENT="management_link"; WAN="wan_link"; LOOPBACK="loopback"; SVI="svi"; UNUSED="unused"
