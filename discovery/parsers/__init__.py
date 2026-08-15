"""Supported V1 vendor parsers for read-only discovery."""

from .aruba_parser import ArubaParser
from .cisco_parser import CiscoParser
from .fortinet_parser import FortinetParser
from .huawei_parser import HuaweiParser
from .juniper_parser import JuniperParser
from .mikrotik_parser import MikroTikParser
from .paloalto_parser import PaloAltoParser

__all__ = [
    "ArubaParser",
    "CiscoParser",
    "FortinetParser",
    "HuaweiParser",
    "JuniperParser",
    "MikroTikParser",
    "PaloAltoParser",
]
