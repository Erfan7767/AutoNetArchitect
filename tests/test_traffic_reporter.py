import tempfile
from pathlib import Path
from traffic_analysis import TrafficOrchestrator, TrafficReporter
from traffic_analysis.models import LinkType, TrafficAnalysisMode

def test_traffic_reporter_exports_json_pdf_and_excel():
    analysis = TrafficOrchestrator().analyze(mode=TrafficAnalysisMode.ESTIMATION, estimation_inputs=[{"link_id":"l1", "source_device":"a", "source_interface":"i", "destination_device":"b", "destination_interface":"i", "link_speed_mbps":1000, "link_type":LinkType.ACCESS_UPLINK, "user_profile_counts":{"office_worker":1}}])
    reporter = TrafficReporter()
    with tempfile.TemporaryDirectory() as directory:
        summary = reporter.summary(analysis, language="ar")
        assert "title" in summary
        json_path = Path(directory)/"report.json"; pdf_path = Path(directory)/"report.pdf"; xlsx_path = Path(directory)/"report.xlsx"
        reporter.to_json(summary, json_path); reporter.to_pdf(summary, pdf_path); reporter.to_excel(analysis, xlsx_path)
        assert json_path.exists() and pdf_path.exists() and xlsx_path.exists()
