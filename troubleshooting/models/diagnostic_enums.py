"""Enumerations used by the Troubleshooting Engine."""

from enum import Enum


class AnalysisMode(str, Enum):
    """Supported evidence collection modes."""

    OFFLINE = "offline"
    PARSED_OUTPUT = "parsed_output"
    LIVE_READ_ONLY = "live_read_only"


class Severity(str, Enum):
    """Incident severity supplied by the requester."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AffectedScopeType(str, Enum):
    """Scope types accepted by a diagnostic session."""

    DEVICE = "device"
    SUBNET = "subnet"
    VLAN = "vlan"
    SITE = "site"
    SERVICE = "service"
    USER = "user"
    UNKNOWN = "unknown"


class SymptomClass(str, Enum):
    """Primary symptom categories."""

    CONNECTIVITY_LOSS = "connectivity_loss"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    AUTHENTICATION_FAILURE = "authentication_failure"
    ROUTING_ISSUE = "routing_issue"
    L2_ISSUE = "l2_issue"
    WIRELESS_ISSUE = "wireless_issue"
    VPN_ISSUE = "vpn_issue"
    DNS_DHCP_ISSUE = "dns_dhcp_issue"
    DEVICE_ISSUE = "device_issue"
    UNKNOWN = "unknown"


class EvidenceSource(str, Enum):
    """Evidence source categories."""

    DESIGN_DATA = "design_data"
    CONFIG_DATA = "config_data"
    PARSED_OUTPUT = "parsed_output"
    LIVE_COLLECTION = "live_collection"
    MONITORING_DATA = "monitoring_data"
    LOG_DATA = "log_data"
    CHANGE_HISTORY = "change_history"
    DIGITAL_TWIN = "digital_twin"
    LEARNING_MEMORY = "learning_memory"
    HUMAN_SUPPLIED = "human_supplied"


class CollectionMethod(str, Enum):
    """How evidence entered the engine."""

    PROVIDED = "provided"
    PARSED = "parsed"
    LIVE_READ_ONLY = "live_read_only"
    DERIVED = "derived"
    UNKNOWN = "unknown"


class DiagnosticStatus(str, Enum):
    """Overall diagnostic lifecycle status."""

    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    BLOCKED_MISSING_EVIDENCE = "blocked_missing_evidence"
    FAILED = "failed"
    NOT_VERIFIABLE = "not_verifiable_with_current_inputs"


class RootCauseClassification(str, Enum):
    """Root cause categories."""

    CONFIGURATION_ERROR = "configuration_error"
    HARDWARE_FAILURE = "hardware_failure"
    SOFTWARE_BUG = "software_bug"
    DESIGN_FLAW = "design_flaw"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    EXTERNAL_FACTOR = "external_factor"
    HUMAN_ERROR = "human_error"
    SECURITY_INCIDENT = "security_incident"
    UNKNOWN = "unknown"


class EscalationTarget(str, Enum):
    """Escalation destinations."""

    VENDOR_TAC = "vendor_tac"
    SECURITY_TEAM = "security_team"
    MANAGEMENT = "management"
    SPECIALIZED_ENGINEERING = "specialized_engineering"
    FIELD_SUPPORT = "field_support"


class WorkflowDirection(str, Enum):
    """Diagnostic search direction."""

    TOP_DOWN = "top_down"
    BOTTOM_UP = "bottom_up"
    DIVIDE_AND_CONQUER = "divide_and_conquer"
