from traffic_analysis import TrafficOrchestrator
from traffic_analysis.models import FlowRecord, LinkType, TrafficAnalysisMode

def test_traffic_orchestrator_estimation_mode_marks_limitations_and_outputs_artifact():
    result = TrafficOrchestrator().analyze(mode=TrafficAnalysisMode.ESTIMATION, estimation_inputs=[{"link_id":"l1", "source_device":"a", "source_interface":"i", "destination_device":"b", "destination_interface":"i", "link_speed_mbps":1000, "link_type":LinkType.ACCESS_UPLINK, "user_profile_counts":{"office_worker":20}}], scope_subjects=["capacity_planning", "dpi"])
    assert result.mode == TrafficAnalysisMode.ESTIMATION
    assert result.links[0].traffic_data.source.value == "estimated"
    assert result.limitations
    assert result.scope_evaluations[1].status.value == "out_of_scope"

def test_traffic_orchestrator_includes_baseline_anomaly_application_and_classification_outputs():
    flow = FlowRecord(source_ip="10.0.0.1", destination_ip="10.0.0.2", protocol="tcp", destination_port=443, bytes_count=100, application="web", evidence_id="ev-flow")
    result = TrafficOrchestrator().analyze(mode=TrafficAnalysisMode.ANALYSIS, flow_records=[flow], baseline_inputs=[{"subject_id":"l1", "metric":"utilization", "period_label":"all", "values":[10,11,9,10], "evidence_ids":["ev-base"]}], anomaly_inputs=[{"subject_id":"l1", "metric":"utilization", "baseline_key":["l1","utilization","all"], "current_value":100}], application_inputs=[{"application_name":"voice", "concurrent_sessions":5}], classification_context=[{"source_zone":"user", "destination_zone":"server"}])
    assert result.traffic_classifications[0].application == "web"
    assert result.application_profiles[0].application_name == "voice"
    assert result.anomalies


def test_traffic_orchestrator_analysis_does_not_invent_links():
    result = TrafficOrchestrator().analyze(mode=TrafficAnalysisMode.ANALYSIS)
    assert result.links == []
    assert result.assumptions
