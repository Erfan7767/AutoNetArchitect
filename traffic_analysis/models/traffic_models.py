"""Pydantic v2 models for Traffic and Capacity Analysis Engine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .traffic_enums import AnomalyType, BottleneckType, CapacityStatus, ClassificationMethod, FindingSeverity, GrowthModel, LinkType, ScopeStatus, TrafficAnalysisMode, TrafficDirection, TrafficPriorityClass, TrafficSource


class TrafficData(BaseModel):
    """Traffic measurement or explicit estimate for one link."""

    model_config = ConfigDict(extra="forbid")

    source: TrafficSource
    avg_utilization_percent: float | None = Field(default=None, ge=0, le=100)
    peak_utilization_percent: float | None = Field(default=None, ge=0, le=100)
    avg_bps_in: int | None = Field(default=None, ge=0)
    avg_bps_out: int | None = Field(default=None, ge=0)
    peak_bps_in: int | None = Field(default=None, ge=0)
    peak_bps_out: int | None = Field(default=None, ge=0)
    measurement_period: timedelta | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
    assumptions: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Ensure collected traffic has a measurement period and evidence."""
        if self.source in {TrafficSource.COLLECTED, TrafficSource.HUMAN_SUPPLIED} and not self.evidence_ids:
            raise ValueError("collected or human-supplied traffic requires evidence_ids")
        if self.source == TrafficSource.COLLECTED and self.measurement_period is None:
            raise ValueError("collected traffic requires measurement_period")
        if self.source == TrafficSource.ESTIMATED and not self.assumptions:
            raise ValueError("estimated traffic requires explicit assumptions")


class TrafficComposition(BaseModel):
    """Traffic composition percentages."""

    model_config = ConfigDict(extra="forbid")

    data_percent: float = Field(default=0.0, ge=0, le=100)
    voice_percent: float = Field(default=0.0, ge=0, le=100)
    video_percent: float = Field(default=0.0, ge=0, le=100)
    management_percent: float = Field(default=0.0, ge=0, le=100)
    other_percent: float = Field(default=0.0, ge=0, le=100)

    def model_post_init(self, __context: Any) -> None:
        """Validate composition total when supplied."""
        total = self.data_percent + self.voice_percent + self.video_percent + self.management_percent + self.other_percent
        if total > 100.01:
            raise ValueError("traffic composition cannot exceed 100 percent")


class TrafficLinkModel(BaseModel):
    """Traffic model for one explicitly identified link."""

    model_config = ConfigDict(extra="forbid")

    link_id: str
    source_device: str
    source_interface: str
    destination_device: str
    destination_interface: str
    link_speed_mbps: float = Field(gt=0)
    link_type: LinkType
    traffic_data: TrafficData
    traffic_composition: TrafficComposition = Field(default_factory=TrafficComposition)
    users_served: int | None = Field(default=None, ge=0)
    devices_served: int | None = Field(default=None, ge=0)
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class TrafficSample(BaseModel):
    """One collected time-series sample."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    interface_id: str
    in_octets: int = Field(ge=0)
    out_octets: int = Field(ge=0)
    in_errors: int = Field(default=0, ge=0)
    out_errors: int = Field(default=0, ge=0)
    in_discards: int = Field(default=0, ge=0)
    out_discards: int = Field(default=0, ge=0)
    evidence_id: str


class FlowRecord(BaseModel):
    """Collected or human-supplied flow record."""

    model_config = ConfigDict(extra="forbid")

    source_ip: str
    destination_ip: str
    protocol: str
    source_port: int | None = Field(default=None, ge=0, le=65535)
    destination_port: int | None = Field(default=None, ge=0, le=65535)
    bytes_count: int = Field(ge=0)
    packets_count: int = Field(default=0, ge=0)
    timestamp: datetime | None = None
    source_subnet: str | None = None
    destination_subnet: str | None = None
    application: str | None = None
    evidence_id: str


class TrafficClassification(BaseModel):
    """Classification result for one flow or traffic group."""

    model_config = ConfigDict(extra="forbid")

    application: str
    priority_class: TrafficPriorityClass
    direction: TrafficDirection
    method: ClassificationMethod
    protocol: str
    port: int | None = None
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class BandwidthRequirement(BaseModel):
    """Required and available bandwidth for one link or service."""

    model_config = ConfigDict(extra="forbid")

    subject_id: str
    current_capacity_mbps: float | None = Field(default=None, ge=0)
    required_bandwidth_mbps: float | None = Field(default=None, ge=0)
    current_utilization_percent: float | None = Field(default=None, ge=0, le=100)
    headroom_percent: float | None = None
    overhead_percent: float = Field(default=0.0, ge=0, le=100)
    upgrade_needed: bool | None = None
    status: CapacityStatus
    contributors: dict[str, float] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class OversubscriptionFinding(BaseModel):
    """Oversubscription assessment."""

    model_config = ConfigDict(extra="forbid")

    subject_id: str
    tier: str
    theoretical_max_input_mbps: float | None = Field(default=None, ge=0)
    actual_uplink_capacity_mbps: float | None = Field(default=None, ge=0)
    ratio: float | None = Field(default=None, ge=0)
    guideline_ratio: float | None = Field(default=None, ge=0)
    status: CapacityStatus
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class BottleneckFinding(BaseModel):
    """Identified or suspected bottleneck."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str
    location: str
    bottleneck_type: BottleneckType
    severity: FindingSeverity
    current_value: float | None = None
    threshold: float | None = None
    impact_description: str
    recommendation: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
    assumptions: list[str] = Field(default_factory=list)


class GrowthProjection(BaseModel):
    """Forecast for a link, device, or service."""

    model_config = ConfigDict(extra="forbid")

    subject_id: str
    model: GrowthModel
    base_value_mbps: float = Field(ge=0)
    projections_mbps: dict[str, float] = Field(default_factory=dict)
    growth_rate_percent_per_year: float | None = None
    threshold_percent: float = Field(default=70.0, ge=0, le=100)
    threshold_breach_period: str | None = None
    historical_evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)


class UpgradeRecommendation(BaseModel):
    """Capacity upgrade recommendation."""

    model_config = ConfigDict(extra="forbid")

    recommendation_id: str
    subject_id: str
    current_capacity_mbps: float | None = None
    required_capacity_mbps: float | None = None
    recommended_solution: str
    target_capacity_mbps: float | None = None
    estimated_cost: str = "unknown"
    implementation_complexity: str
    required_downtime: str = "unknown"
    recommended_timeline: str
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    production_approval_required: bool = True


class BaselineStatistics(BaseModel):
    """Statistical baseline for one metric."""

    model_config = ConfigDict(extra="forbid")

    subject_id: str
    metric: str
    period_label: str
    sample_count: int = Field(ge=0)
    average: float | None = None
    median: float | None = None
    percentile_95: float | None = None
    standard_deviation: float | None = Field(default=None, ge=0)
    minimum: float | None = None
    maximum: float | None = None
    source_evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class TrafficAnomaly(BaseModel):
    """Traffic anomaly finding."""

    model_config = ConfigDict(extra="forbid")

    anomaly_id: str
    anomaly_type: AnomalyType
    severity: FindingSeverity
    detected_at: datetime
    metric: str
    expected_value: float | str | None = None
    actual_value: float | str | None = None
    deviation: float | str | None = None
    possible_causes: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
    incident_creation_recommended: bool = False


class ApplicationProfile(BaseModel):
    """Application traffic profile."""

    model_config = ConfigDict(extra="forbid")

    application_name: str
    protocol: str
    port: int | None = None
    avg_session_bandwidth_mbps: float | None = Field(default=None, ge=0)
    peak_session_bandwidth_mbps: float | None = Field(default=None, ge=0)
    concurrent_sessions_estimate: int | None = Field(default=None, ge=0)
    total_bandwidth_estimate_mbps: float | None = Field(default=None, ge=0)
    latency_sensitivity: str
    loss_sensitivity: str
    jitter_sensitivity: str
    qos_class_mapping: TrafficPriorityClass
    source: TrafficSource
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class FlowAnalysisReport(BaseModel):
    """Flow analysis output."""

    model_config = ConfigDict(extra="forbid")

    available: bool
    top_source_ips: list[dict[str, Any]] = Field(default_factory=list)
    top_destination_ips: list[dict[str, Any]] = Field(default_factory=list)
    top_pairs: list[dict[str, Any]] = Field(default_factory=list)
    top_applications: list[dict[str, Any]] = Field(default_factory=list)
    traffic_matrix: list[dict[str, Any]] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class QoSQueueFinding(BaseModel):
    """QoS queue utilization finding."""

    model_config = ConfigDict(extra="forbid")

    interface_id: str
    queue_or_class: str
    queue_depth: float | None = None
    packets_queued: int | None = Field(default=None, ge=0)
    packets_dropped: int | None = Field(default=None, ge=0)
    bandwidth_consumed_mbps: float | None = Field(default=None, ge=0)
    bandwidth_allocated_mbps: float | None = Field(default=None, ge=0)
    status: CapacityStatus
    finding: str
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class WANUtilizationFinding(BaseModel):
    """WAN link utilization finding."""

    model_config = ConfigDict(extra="forbid")

    link_id: str
    utilization_percent: float | None = Field(default=None, ge=0, le=100)
    peak_utilization_percent: float | None = Field(default=None, ge=0, le=100)
    data_percent: float | None = Field(default=None, ge=0, le=100)
    voice_percent: float | None = Field(default=None, ge=0, le=100)
    video_percent: float | None = Field(default=None, ge=0, le=100)
    cir_utilization_percent: float | None = Field(default=None, ge=0, le=100)
    burst_utilization_percent: float | None = Field(default=None, ge=0, le=100)
    vpn_utilization_percent: float | None = Field(default=None, ge=0, le=100)
    cost_per_mbps: float | None = Field(default=None, ge=0)
    status: CapacityStatus
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ScopeEvaluation(BaseModel):
    """Scope-control decision for a traffic analysis request."""

    model_config = ConfigDict(extra="forbid")

    status: ScopeStatus
    subject: str
    reason: str
    required_human_action: str | None = None
    preview_only: bool = False
    decision_id: str


class TrafficAnalysis(BaseModel):
    """Complete traffic analysis artifact."""

    model_config = ConfigDict(extra="forbid")

    analysis_id: str
    mode: TrafficAnalysisMode
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    links: list[TrafficLinkModel] = Field(default_factory=list)
    bandwidth_requirements: list[BandwidthRequirement] = Field(default_factory=list)
    oversubscription_findings: list[OversubscriptionFinding] = Field(default_factory=list)
    bottlenecks: list[BottleneckFinding] = Field(default_factory=list)
    growth_projections: list[GrowthProjection] = Field(default_factory=list)
    upgrade_recommendations: list[UpgradeRecommendation] = Field(default_factory=list)
    anomalies: list[TrafficAnomaly] = Field(default_factory=list)
    application_profiles: list[ApplicationProfile] = Field(default_factory=list)
    traffic_classifications: list[TrafficClassification] = Field(default_factory=list)
    flow_analysis: FlowAnalysisReport | None = None
    qos_findings: list[QoSQueueFinding] = Field(default_factory=list)
    wan_findings: list[WANUtilizationFinding] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    assumptions: list[dict[str, Any]] = Field(default_factory=list)
    scope_evaluations: list[ScopeEvaluation] = Field(default_factory=list)
