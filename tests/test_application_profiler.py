from traffic_analysis.application_profiler import ApplicationProfiler

def test_application_profiler_default_and_total_bandwidth():
    result = ApplicationProfiler().profile(application_name="voice", concurrent_sessions=10)
    assert result.total_bandwidth_estimate_mbps == 1.2
    assert result.qos_class_mapping.value == "real_time"

def test_application_profiler_requires_human_custom_profile():
    try:
        ApplicationProfiler().profile(application_name="custom", custom={"protocol":"tcp"})
    except ValueError as error:
        assert "HumanSuppliedMandatory" in str(error)
    else:
        raise AssertionError("custom profile must require human validation")
