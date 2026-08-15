from incident_response.timeline_recorder import TimelineRecorder


def test_timeline_recorder_is_append_only_and_immutable():
    recorder = TimelineRecorder()
    entry = recorder.record("INC-20260814-0001", event_type="detection", description="detected", performed_by="operator")
    assert len(recorder.list("INC-20260814-0001")) == 1
    try:
        entry.description = "changed"
    except Exception:
        pass
    else:
        raise AssertionError("timeline entry must be immutable")
