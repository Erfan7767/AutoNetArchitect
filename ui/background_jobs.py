"""Local background job coordination for the V1 UI shell."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from concurrent.futures import Future, ThreadPoolExecutor
import threading
import traceback
import uuid
from typing import Any, Callable, Mapping

from .state_manager import mask_for_ui


class JobStatus(str, Enum):
    """Supported local background job states."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobRecord:
    """Secret-safe metadata for one background job."""

    job_id: str
    name: str
    status: JobStatus
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    result: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize job metadata for UI display."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "result": mask_for_ui(self.result),
            "error": self.error,
            "metadata": mask_for_ui(self.metadata),
        }


JobCallable = Callable[..., Any]


class BackgroundJobManager:
    """Run UI-triggered service calls on one local worker with inspectable state."""

    def __init__(self, *, max_workers: int = 1) -> None:
        """Create a bounded worker pool suitable for a local single-user session."""
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="autonet-ui")
        self._records: dict[str, JobRecord] = {}
        self._futures: dict[str, Future[Any]] = {}
        self._lock = threading.RLock()
        self._closed = False

    def submit(self, name: str, function: JobCallable, *args: Any, metadata: Mapping[str, Any] | None = None, **kwargs: Any) -> str:
        """Queue one callable and return a job identifier immediately."""
        if self._closed:
            raise RuntimeError("background job manager is closed")
        if not name or not callable(function):
            raise ValueError("name and callable function are required")
        job_id = f"job:{uuid.uuid4()}"
        record = JobRecord(job_id=job_id, name=name, status=JobStatus.QUEUED, created_at=datetime.now(timezone.utc).isoformat(), metadata=dict(metadata or {}))
        with self._lock:
            self._records[job_id] = record
            self._futures[job_id] = self._executor.submit(self._run, job_id, function, args, kwargs)
        return job_id

    def get(self, job_id: str) -> JobRecord:
        """Return a detached job record or raise for an unknown identifier."""
        with self._lock:
            if job_id not in self._records:
                raise KeyError(f"unknown job: {job_id}")
            record = self._records[job_id]
            return JobRecord(record.job_id, record.name, record.status, record.created_at, record.started_at, record.finished_at, mask_for_ui(record.result), record.error, mask_for_ui(record.metadata))

    def list(self) -> tuple[JobRecord, ...]:
        """Return all jobs in creation order."""
        with self._lock:
            return tuple(self.get(job_id) for job_id in self._records)

    def cancel(self, job_id: str) -> bool:
        """Cancel a queued job when the executor has not started it."""
        with self._lock:
            future = self._futures.get(job_id)
            if future is None:
                raise KeyError(f"unknown job: {job_id}")
            cancelled = future.cancel()
            if cancelled:
                record = self._records[job_id]
                record.status = JobStatus.CANCELLED
                record.finished_at = datetime.now(timezone.utc).isoformat()
            return cancelled

    def wait(self, job_id: str, timeout: float | None = None) -> JobRecord:
        """Wait for one job and return its sanitized record."""
        with self._lock:
            future = self._futures.get(job_id)
            if future is None:
                raise KeyError(f"unknown job: {job_id}")
        future.result(timeout=timeout)
        return self.get(job_id)

    def shutdown(self, *, wait: bool = True) -> None:
        """Stop accepting jobs and release worker resources."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._executor.shutdown(wait=wait, cancel_futures=True)

    def _run(self, job_id: str, function: JobCallable, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        """Execute one callable and persist secret-safe outcome metadata."""
        with self._lock:
            record = self._records[job_id]
            record.status = JobStatus.RUNNING
            record.started_at = datetime.now(timezone.utc).isoformat()
        try:
            result = function(*args, **kwargs)
        except Exception as exc:
            with self._lock:
                record = self._records[job_id]
                record.status = JobStatus.FAILED
                record.finished_at = datetime.now(timezone.utc).isoformat()
                record.error = f"{type(exc).__name__}: {exc}"
                record.metadata["traceback"] = traceback.format_exc(limit=3)
            return None
        with self._lock:
            record = self._records[job_id]
            record.status = JobStatus.SUCCEEDED
            record.finished_at = datetime.now(timezone.utc).isoformat()
            record.result = mask_for_ui(result)
        return result

    def __enter__(self) -> "BackgroundJobManager":
        """Use the manager in a bounded context."""
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback_value: Any) -> None:
        """Shutdown the worker pool at context exit."""
        self.shutdown()
