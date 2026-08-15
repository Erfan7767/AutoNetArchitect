from change_management import ChangeHistory


def test_change_history_appends_hash_chain_and_supports_search():
    history = ChangeHistory()
    history.record("CHG-26", "created", "alice", {"requester": "alice", "device_id": "edge-1", "password": "should-not-remain"})
    history.record("CHG-26", "approved", "bob", {"status": "approved", "change_type": "normal"})
    assert history.verify_integrity() is True
    assert len(history.query(device_id="edge-1")) == 1
    assert "should-not-remain" not in str(history.entries()[0].details)
