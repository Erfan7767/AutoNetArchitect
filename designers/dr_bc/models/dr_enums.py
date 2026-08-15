from enum import Enum
class DRStrategy(str,Enum):
    ACTIVE_ACTIVE="active_active"; HOT="hot_standby"; WARM="warm_standby"; COLD="cold_standby"; PILOT="pilot_light"
