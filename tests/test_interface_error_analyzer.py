from troubleshooting.interface_error_analyzer import InterfaceErrorAnalyzer


def test_interface_error_analyzer_reports_crc_and_drops():
    result = InterfaceErrorAnalyzer().analyze({"Gi1/0/1": {"crc": 3, "output_drops": 10}})
    assert len(result.findings) == 2
    assert {item.error_type for item in result.findings} == {"crc", "output_drops"}


def test_interface_error_analyzer_does_not_report_zero_counters():
    result = InterfaceErrorAnalyzer().analyze({"Gi1/0/1": {"crc": 0}})
    assert result.findings == []
