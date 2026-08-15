"""Shared helpers for secret-safe bilingual reporting."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence
import uuid

from log_redaction.redacting_filter import RedactingFilter

from .report_models import ReportLanguage, ReportMetadata


def localized(language: ReportLanguage | str, english: str, arabic: str) -> str:
    """Return a localized label or a bilingual label."""
    selected = ReportLanguage(language)
    if selected == ReportLanguage.ARABIC:
        return arabic
    if selected == ReportLanguage.BOTH:
        return f"{english} / {arabic}"
    return english


def sanitize(value: Any) -> Any:
    """Recursively redact sensitive values while preserving secret:// references."""
    return RedactingFilter.sanitize_value(value)


def safe_json(value: Any) -> str:
    """Serialize a sanitized value deterministically."""
    return json.dumps(sanitize(value), indent=2, ensure_ascii=False, sort_keys=True, default=str) + "\n"


def write_text(path: str | Path, text: str) -> str:
    """Write UTF-8 text atomically."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(target)
    return str(target)


def write_json(path: str | Path, value: Any) -> str:
    """Write a sanitized JSON artifact."""
    return write_text(path, safe_json(value))


def file_sha256(path: str | Path) -> str:
    """Calculate a file SHA-256 digest."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def metadata(*, title: str, language: ReportLanguage | str, sot_basis: Mapping[str, str] | None, evidence_basis: Sequence[str], disclaimer: str | None = None) -> ReportMetadata:
    """Build mandatory report metadata."""
    return ReportMetadata(report_id=f"report:{uuid.uuid4()}", title=title, language=ReportLanguage(language), generated_at=datetime.now(timezone.utc), sot_basis=dict(sot_basis or {}), evidence_basis=list(dict.fromkeys(str(item) for item in evidence_basis)), redaction_applied=True, secret_values_included=False, disclaimer=disclaimer or "Generated from supplied project records only; absence of a record is not evidence that the underlying state exists.")


def manifest(directory: str | Path, *, source_domain: str) -> list[dict[str, Any]]:
    """Return a deterministic manifest of files under a directory."""
    root = Path(directory)
    result = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        result.append({"relative_path": str(path.relative_to(root)), "sha256": file_sha256(path), "source_domain": source_domain, "redacted": True})
    return result


def assert_safe_text(text: str) -> None:
    """Reject common raw-secret patterns in generated content."""
    if not isinstance(text, str):
        raise TypeError("report content must be text")
    redacted = RedactingFilter.redact_text(text)
    if redacted != text:
        raise ValueError("unredacted sensitive material was detected in report content")
