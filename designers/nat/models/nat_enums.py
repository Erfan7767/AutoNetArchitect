from enum import Enum
class NATType(str,Enum):
    SOURCE="source"; DESTINATION="destination"; STATIC="static"; PAT="pat"; POLICY="policy"; EXEMPTION="exemption"
