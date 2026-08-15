"""Canonical project constants."""
from typing import Final
SCHEMA_VERSION: Final[str] = "1.0.0"
PROJECT_NAME: Final[str] = "AutoNetArchitect"
SUPPORTED_VENDORS: Final[tuple[str, ...]] = ("Huawei",)
DEFAULT_TIMEOUT_SECONDS: Final[float] = 30.0
MIN_VLAN: Final[int] = 1
MAX_VLAN: Final[int] = 4094
MIN_PORT: Final[int] = 1
MAX_PORT: Final[int] = 65535
