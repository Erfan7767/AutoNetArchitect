"""Traffic and Capacity Analysis orchestration."""
from __future__ import annotations
from datetime import datetime, timezone
import uuid
from typing import Any, Mapping, Sequence
from audit.audit_trail import AuditTrail
from designers.base_designer import Assumption, DecisionRecord
from ._common import assumption_dict, decision_dict, make_assumption, make_decision
from .models import FlowRecord, GrowthModel, LinkType, ScopeEvaluation, TrafficAnalysis, TrafficAnalysisMode, TrafficLinkModel, TrafficSource
from .traffic_model import TrafficModelRegistry
from .traffic_estimator import TrafficEstimator
from .traffic_collector import TrafficCollection
from .traffic_classifier import TrafficClassifier
from .bandwidth_calculator import BandwidthCalculator
from .oversubscription_analyzer import OversubscriptionAnalyzer
from .bottleneck_detector import BottleneckDetector
from .growth_projector import GrowthProjector
from .upgrade_recommender import UpgradeRecommender
from .capacity_planner import CapacityPlanner
from .flow_analyzer import FlowAnalyzer
from .qos_utilization_analyzer import QoSUtilizationAnalyzer
from .wan_utilization_analyzer import WANUtilizationAnalyzer
from .traffic_scope_boundary import TrafficScopeBoundary
from .traffic_reporter import TrafficReporter
from .baseline_manager import BaselineManager
from .anomaly_detector import AnomalyDetector
from .application_profiler import ApplicationProfiler

class TrafficOrchestrator:
    """Coordinate estimation and analysis modes without inventing collected traffic."""
    def __init__(self, *, audit_trail: AuditTrail | None = None) -> None:
        """Initialize all traffic analysis engines."""
        self.audit_trail = audit_trail
        self.model_registry = TrafficModelRegistry(); self.estimator = TrafficEstimator(); self.classifier = TrafficClassifier(); self.bandwidth = BandwidthCalculator(); self.oversubscription = OversubscriptionAnalyzer(); self.bottleneck = BottleneckDetector(); self.growth = GrowthProjector(); self.recommender = UpgradeRecommender(); self.capacity = CapacityPlanner(self.recommender); self.flow = FlowAnalyzer(); self.qos = QoSUtilizationAnalyzer(); self.wan = WANUtilizationAnalyzer(); self.scope = TrafficScopeBoundary(); self.reporter = TrafficReporter(); self.baseline = BaselineManager(); self.anomaly = AnomalyDetector(); self.application = ApplicationProfiler()
        self.decisions: list[DecisionRecord] = []; self.assumptions: list[Assumption] = []
    def analyze(self, *, mode: TrafficAnalysisMode | str, links: Sequence[TrafficLinkModel] = (), estimation_inputs: Sequence[Mapping[str, Any]] = (), collection: TrafficCollection | None = None, flow_records: Sequence[FlowRecord] = (), required_by_link: Mapping[str, float] | None = None, growth_inputs: Mapping[str, Mapping[str, Any]] | None = None, observations: Mapping[str, Mapping[str, float]] | None = None, oversubscription_inputs: Sequence[Mapping[str, Any]] = (), qos_queues: Sequence[Mapping[str, object]] = (), baseline_inputs: Sequence[Mapping[str, Any]] = (), anomaly_inputs: Sequence[Mapping[str, Any]] = (), application_inputs: Sequence[Mapping[str, Any]] = (), classification_context: Sequence[Mapping[str, Any]] = (), domain: str = "enterprise_office", scope_subjects: Sequence[str] = ()) -> TrafficAnalysis:
        """Run the complete analysis pipeline in estimation or evidence analysis mode."""
        analysis_mode = TrafficAnalysisMode(mode)
        selected_links = list(links)
        if analysis_mode == TrafficAnalysisMode.ESTIMATION:
            for item in estimation_inputs:
                selected_links.append(self.estimator.estimate_link(**dict(item)))
            if not estimation_inputs and not selected_links:
                self.assumptions.append(make_assumption("traffic-orchestrator:estimation-inputs", "missing", "estimation mode requires explicit link/profile inputs", True))
        else:
            if collection is not None and collection.samples:
                self.assumptions.append(make_assumption("traffic-orchestrator:collection", "supplied", "collection samples are accepted as evidence but link aggregation remains caller-owned", True))
            if not selected_links:
                self.assumptions.append(make_assumption("traffic-orchestrator:analysis-links", "missing", "analysis mode cannot infer links without explicit traffic link models", True))
            if any(link.traffic_data.source == TrafficSource.ESTIMATED for link in selected_links):
                self.assumptions.append(make_assumption("traffic-orchestrator:estimated-link-in-analysis", True, "estimated links are retained but not treated as collected evidence", True))
        bandwidth = [self.bandwidth.calculate_link(link) for link in selected_links]
        oversub = [self.oversubscription.analyze(subject_id=str(item["subject_id"]), tier=str(item["tier"]), downstream_capacities_mbps=[float(value) for value in item["downstream_capacities_mbps"]], uplink_capacity_mbps=float(item["uplink_capacity_mbps"]), domain=domain) for item in oversubscription_inputs]
        bottlenecks = self.bottleneck.detect(selected_links, observations=observations)
        forecasts = []
        for link in selected_links:
            growth = (growth_inputs or {}).get(link.link_id, {})
            forecasts.append(self.growth.project(subject_id=link.link_id, current_mbps=max(link.traffic_data.peak_bps_in or 0, link.traffic_data.peak_bps_out or 0) / 1_000_000, model=GrowthModel(growth.get("model", GrowthModel.EXPONENTIAL.value)), annual_growth_rate_percent=growth.get("annual_growth_rate_percent"), historical_values_mbps=growth.get("historical_values_mbps", [])))
        required = dict(required_by_link or {item.subject_id: float(item.required_bandwidth_mbps or 0) for item in bandwidth})
        plan = self.capacity.plan(links=selected_links, required_by_link=required, forecasts=forecasts)
        baseline_map = {}
        for item in baseline_inputs:
            baseline_item = self.baseline.create(**dict(item))
            baseline_map[(baseline_item.subject_id, baseline_item.metric, baseline_item.period_label)] = baseline_item
        anomalies = []
        for item in anomaly_inputs:
            input_item = dict(item)
            baseline_key = tuple(input_item.pop("baseline_key", ()))
            baseline_item = baseline_map.get(baseline_key) if baseline_key else None
            anomalies.extend(self.anomaly.detect(baseline=baseline_item, **input_item))
        application_profiles = [self.application.profile(**dict(item)) for item in application_inputs]
        classifications = []
        for index, flow in enumerate(flow_records):
            context = dict(classification_context[index]) if index < len(classification_context) else {}
            classifications.append(self.classifier.classify(flow, source_zone=context.get("source_zone"), destination_zone=context.get("destination_zone"), dscp=context.get("dscp")))
        flow_report = self.flow.analyze(flow_records)
        qos_findings = self.qos.analyze(qos_queues)
        wan_findings = self.wan.analyze(selected_links)
        scopes = [self.scope.check(subject) for subject in scope_subjects]
        limitations = list(dict.fromkeys(["estimation mode does not prove actual traffic", "DPI/APM/EUEM/packet capture/content inspection are out of scope", *flow_report.assumptions, *[item.reason for item in scopes if item.status.value != "in_scope"]]))
        evidence = list(dict.fromkeys([evidence_id for link in selected_links for evidence_id in [*link.traffic_data.evidence_ids, *link.evidence_ids]]))
        all_decisions = [self._serialize_decision(item) for item in [*self.estimator.decisions, *self.bandwidth.decisions, *self.oversubscription.decisions, *self.bottleneck.decisions, *self.growth.decisions, *self.capacity.decisions, *self.flow.decisions, *self.qos.decisions, *self.wan.decisions, *self.baseline.decisions, *self.anomaly.decisions, *self.application.decisions, *self.classifier.decisions, *self.scope.decisions]]
        all_assumptions = [assumption_dict(item) for item in [*self.estimator.assumptions, *self.bandwidth.assumptions, *self.oversubscription.assumptions, *self.bottleneck.assumptions, *self.growth.assumptions, *self.capacity.assumptions, *self.flow.assumptions, *self.qos.assumptions, *self.wan.assumptions, *self.baseline.assumptions, *self.anomaly.assumptions, *self.application.assumptions, *self.classifier.assumptions, *self.assumptions]]
        result = TrafficAnalysis(analysis_id=f"traffic:{uuid.uuid4()}", mode=analysis_mode, created_at=datetime.now(timezone.utc), links=selected_links, bandwidth_requirements=bandwidth, oversubscription_findings=oversub, bottlenecks=bottlenecks, growth_projections=forecasts, upgrade_recommendations=plan.recommendations, anomalies=anomalies, application_profiles=application_profiles, traffic_classifications=classifications, flow_analysis=flow_report, qos_findings=qos_findings, wan_findings=wan_findings, limitations=limitations, evidence_ids=evidence, decisions=all_decisions, assumptions=all_assumptions, scope_evaluations=scopes)
        decision = make_decision("TrafficOrchestrator", result.analysis_id, analysis_mode.value, "run estimation or analysis pipeline while preserving source and limitation labels", ["estimation", "analysis"], {item.value: "not selected by requested mode" for item in TrafficAnalysisMode if item != analysis_mode})
        self.decisions.append(decision)
        result.decisions.append(self._serialize_decision(decision))
        if self.audit_trail is not None:
            self.audit_trail.record("traffic.analysis", "traffic-orchestrator", {"analysis_id": result.analysis_id, "mode": result.mode.value, "link_count": len(result.links), "evidence_ids": result.evidence_ids, "estimation_only": result.mode == TrafficAnalysisMode.ESTIMATION}, outcome="success", correlation_id=result.analysis_id)
        return result
    @staticmethod
    def _serialize_decision(decision: DecisionRecord) -> dict[str, Any]:
        return decision_dict(decision)
