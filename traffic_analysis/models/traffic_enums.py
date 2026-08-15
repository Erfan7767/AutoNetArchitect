"""Enumerations for Traffic and Capacity Analysis Engine."""

from enum import Enum


class TrafficSource(str, Enum):
    """Origin of a traffic measurement."""

    ESTIMATED = "estimated"
    COLLECTED = "collected"
    HUMAN_SUPPLIED = "human_supplied"


class TrafficAnalysisMode(str, Enum):
    """Operating mode of traffic analysis."""

    ESTIMATION = "estimation"
    ANALYSIS = "analysis"


class LinkType(str, Enum):
    """Network link tier."""

    ACCESS_UPLINK = "access_uplink"
    DISTRIBUTION_UPLINK = "distribution_uplink"
    CORE_LINK = "core_link"
    WAN_LINK = "wan_link"
    SERVER_LINK = "server_link"
    UNKNOWN = "unknown"


class TrafficPriorityClass(str, Enum):
    """Traffic priority class."""

    REAL_TIME = "real_time"
    BUSINESS_CRITICAL = "business_critical"
    DEFAULT = "default"
    BEST_EFFORT = "best_effort"
    SCAVENGER = "scavenger"


class TrafficDirection(str, Enum):
    """Traffic direction classification."""

    NORTH_SOUTH = "north_south"
    EAST_WEST = "east_west"
    MANAGEMENT = "management"
    UNKNOWN = "unknown"


class ClassificationMethod(str, Enum):
    """Method used for traffic classification."""

    PORT_BASED = "port_based"
    DSCP_BASED = "dscp_based"
    DPI_OR_NBAR = "dpi_or_nbar"
    FLOW_BASED = "flow_based"
    HUMAN_SUPPLIED = "human_supplied"
    UNKNOWN = "unknown"


class BottleneckType(str, Enum):
    """Bottleneck class."""

    BANDWIDTH = "bandwidth_bottleneck"
    CPU = "cpu_bottleneck"
    MEMORY = "memory_bottleneck"
    SESSION = "session_bottleneck"
    QOS = "qos_bottleneck"
    UNKNOWN = "unknown"


class FindingSeverity(str, Enum):
    """Finding severity."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """Traffic anomaly class."""

    TRAFFIC_SPIKE = "traffic_spike"
    TRAFFIC_DROP = "traffic_drop"
    UNUSUAL_PROTOCOL = "unusual_protocol"
    UNUSUAL_DESTINATION = "unusual_destination"
    UNUSUAL_TIME = "unusual_time"
    BROADCAST_STORM = "broadcast_storm"


class GrowthModel(str, Enum):
    """Projection model."""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    STEP = "step"
    SEASONAL = "seasonal"


class CapacityStatus(str, Enum):
    """Capacity assessment state."""

    HEALTHY = "healthy"
    WARNING = "warning"
    UPGRADE_REQUIRED = "upgrade_required"
    UNKNOWN = "unknown"


class ScopeStatus(str, Enum):
    """Traffic analysis scope result."""

    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    PREVIEW_ONLY = "preview_only"
