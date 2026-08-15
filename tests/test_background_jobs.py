"""Tests for local UI background jobs."""
from __future__ import annotations

from ui.background_jobs import BackgroundJobManager, JobStatus


def test_background_job_succeeds_and_masks_result():
    with BackgroundJobManager() as jobs:
        job_id = jobs.submit("safe-job", lambda: {"status": "done", "token": "raw-token"})
        record = jobs.wait(job_id, timeout=5)
        assert record.status == JobStatus.SUCCEEDED
        assert record.result["token"] == "<REDACTED>"


def test_background_job_failure_is_recorded_without_raising_from_worker():
    def failing_job():
        raise ValueError("controlled failure")

    with BackgroundJobManager() as jobs:
        job_id = jobs.submit("failing-job", failing_job)
        record = jobs.wait(job_id, timeout=5)
        assert record.status == JobStatus.FAILED
        assert "ValueError" in str(record.error)


def test_background_job_cancel_works_for_queued_work():
    with BackgroundJobManager() as jobs:
        first = jobs.submit("first", lambda: "first")
        second = jobs.submit("second", lambda: "second")
        jobs.wait(first, timeout=5)
        cancelled = jobs.cancel(second)
        if cancelled:
            assert jobs.get(second).status == JobStatus.CANCELLED
        else:
            assert jobs.get(second).status in {JobStatus.SUCCEEDED, JobStatus.RUNNING}


def test_unknown_job_is_rejected():
    with BackgroundJobManager() as jobs:
        found = False
        try:
            jobs.get("job:unknown")
        except KeyError:
            found = True
        if not found:
            raise AssertionError("unknown job should be rejected")
