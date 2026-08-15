"""Routing enums."""
from enum import Enum
class Protocol(str,Enum):
    OSPF="ospf"; EIGRP="eigrp"; ISIS="isis"; STATIC="static"
class OSPFAreaType(str,Enum):
    REGULAR="regular"; STUB="stub"; TOTALLY_STUB="totally_stub"; NSSA="nssa"; TOTALLY_NSSA="totally_nssa"
class NetworkType(str,Enum):
    BROADCAST="broadcast"; POINT_TO_POINT="point_to_point"; NBMA="nbma"; POINT_TO_MULTIPOINT="point_to_multipoint"
