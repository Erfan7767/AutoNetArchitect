from troubleshooting.log_analyzer import LogAnalyzer


def test_log_analyzer_extracts_known_patterns():
    report = LogAnalyzer().analyze(["2026-01-01T00:00:00Z %LINK-3-UPDOWN: interface down", "2026-01-01T00:00:20Z %OSPF-5-ADJCHG: neighbor down"], device_id="r1")
    assert len(report.events) == 2
    assert report.patterns
    assert report.correlated_groups


def test_log_analyzer_marks_missing_timestamps():
    report = LogAnalyzer().analyze(["%SYS-5-RELOAD: reload"])
    assert report.assumptions
