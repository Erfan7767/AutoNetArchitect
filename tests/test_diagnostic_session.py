from troubleshooting.diagnostic_session import DiagnosticSession


def test_diagnostic_session_records_lifecycle():
    session = DiagnosticSession("diag-1", "tester")
    session.transition("classified", "classified")
    session.transition("completed", "done", ["ev-1"])
    exported = session.export()
    assert exported["state"] == "completed"
    assert len(exported["events"]) == 2
