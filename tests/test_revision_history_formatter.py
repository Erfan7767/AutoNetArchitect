from documentation.formatters.revision_history_formatter import RevisionHistoryFormatter

def test_revision_history_has_pending_when_not_supplied():
    assert RevisionHistoryFormatter().format()[0]["approved_by"] == "PENDING"
