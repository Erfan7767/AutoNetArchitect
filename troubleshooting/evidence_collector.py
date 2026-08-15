"""Evidence collection for offline, parsed-output, and live read-only analysis."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any, Callable, Iterable, Mapping, Sequence

from designers.base_designer import Assumption, DecisionRecord
from log_redaction.redacting_filter import RedactingFilter

from .models import AnalysisMode, CollectionMethod, EvidenceCollection, EvidenceItem, EvidenceRequest, EvidenceSource


LiveCollector = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class EvidenceCollector:
    """Collect only supplied or read-only evidence and preserve source traceability."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def collect(
        self,
        mode: AnalysisMode | str,
        requests: Sequence[EvidenceRequest] = (),
        *,
        design_data: Mapping[str, Any] | None = None,
        config_data: Mapping[str, Any] | None = None,
        parsed_output: Sequence[Mapping[str, Any]] = (),
        monitoring_data: Sequence[Mapping[str, Any]] = (),
        log_data: Sequence[Mapping[str, Any]] = (),
        change_history: Sequence[Mapping[str, Any]] = (),
        digital_twin_data: Sequence[Mapping[str, Any]] = (),
        learning_memory: Sequence[Mapping[str, Any]] = (),
        live_collector: LiveCollector | None = None,
    ) -> EvidenceCollection:
        """Collect evidence according to mode; live mode is explicitly read-only."""
        normalized = AnalysisMode(mode)
        items: list[EvidenceItem] = []
        normalized_requests = list(requests)
        if design_data is not None:
            items.append(self._item("design:provided", EvidenceSource.DESIGN_DATA, design_data, design_data, CollectionMethod.PROVIDED, 0.8))
        if config_data is not None:
            items.append(self._item("config:provided", EvidenceSource.CONFIG_DATA, config_data, config_data, CollectionMethod.PROVIDED, 0.8))
        items.extend(self._provided_items("parsed", EvidenceSource.PARSED_OUTPUT, parsed_output, CollectionMethod.PARSED, 0.85))
        items.extend(self._provided_items("monitoring", EvidenceSource.MONITORING_DATA, monitoring_data, CollectionMethod.PROVIDED, 0.7))
        items.extend(self._provided_items("logs", EvidenceSource.LOG_DATA, log_data, CollectionMethod.PROVIDED, 0.75))
        items.extend(self._provided_items("changes", EvidenceSource.CHANGE_HISTORY, change_history, CollectionMethod.PROVIDED, 0.75))
        items.extend(self._provided_items("twin", EvidenceSource.DIGITAL_TWIN, digital_twin_data, CollectionMethod.PROVIDED, 0.65))
        items.extend(self._provided_items("memory", EvidenceSource.LEARNING_MEMORY, learning_memory, CollectionMethod.PROVIDED, 0.55))
        missing: list[str] = []
        if normalized == AnalysisMode.LIVE_READ_ONLY:
            if live_collector is None:
                self.assumptions.append(Assumption("live_collector", "not_supplied", "V1 does not fabricate live device output", True))
                missing.extend(request.evidence_type for request in normalized_requests if request.required)
            else:
                for request in normalized_requests:
                    payload = {"operation": "collect_evidence", "read_only": True, "request": request.model_dump(mode="json")}
                    try:
                        response = dict(live_collector(payload))
                        if bool(response.get("write_attempted", False)) or str(response.get("operation", "collect_evidence")).lower() not in {"collect_evidence", "show", "display", "get", "health_check", "discover", "verify"}:
                            self.assumptions.append(Assumption(f"live:{request.evidence_type}", "blocked_non_read_only", "the supplied live collector did not provide a verified read-only operation", True))
                            missing.append(request.evidence_type)
                            continue
                        parsed = response.get("parsed_data", response.get("values", {}))
                        raw = RedactingFilter.sanitize_value(response.get("raw_data", response.get("output", "")))
                        item = self._item(f"live:{request.target_device}:{request.evidence_type}", EvidenceSource.LIVE_COLLECTION, raw, parsed if isinstance(parsed, dict) else {"value": parsed}, CollectionMethod.LIVE_READ_ONLY, float(response.get("confidence", 0.8)), request.target_device, request.command_or_query).model_copy(update={"request_type": request.evidence_type})
                        items.append(item)
                    except Exception:
                        missing.append(request.evidence_type)
                        self.assumptions.append(Assumption(f"live:{request.evidence_type}", "collection_failed", "live collection failure is not converted into a healthy state", True))
        elif normalized == AnalysisMode.OFFLINE:
            if parsed_output:
                self.assumptions.append(Assumption("offline_parsed_output", "provided_but_not_live", "offline analysis treats parsed output as supplied evidence, not fresh device state", True))
        elif normalized == AnalysisMode.PARSED_OUTPUT and not parsed_output:
            missing.extend(request.evidence_type for request in normalized_requests if request.required)
        available_types = {item.request_type or item.source.value for item in items}
        for request in normalized_requests:
            if request.required and not any(request.evidence_type in item.request_type or request.evidence_type in item.source.value for item in items):
                missing.append(request.evidence_type)
        complete = not missing
        self.decisions.append(DecisionRecord("EvidenceCollector", f"evidence-collection:{normalized.value}", "read_only_collection", "only supplied evidence and explicitly read-only collection are allowed", ["read_only_collection", "write_collection"], {"read_only_collection": "selected by V1 safety policy", "write_collection": "always rejected"}))
        if missing:
            self.assumptions.append(Assumption("missing_evidence", sorted(set(missing)), "diagnosis remains bounded because required evidence is unavailable", True))
        return EvidenceCollection(items=items, requests=normalized_requests, mode=normalized.value, complete=complete, missing_required=sorted(set(missing)), assumptions=[item.key for item in self.assumptions])

    @staticmethod
    def _item(identifier: str, source: EvidenceSource, raw: Any, parsed: Any, method: CollectionMethod, confidence: float, target_device: str = "", command: str = "") -> EvidenceItem:
        """Build one sanitized, hashed evidence item."""
        sanitized_raw = RedactingFilter.sanitize_value(raw)
        evidence_hash = hashlib.sha256(str(sanitized_raw).encode("utf-8")).hexdigest()
        return EvidenceItem(evidence_id=identifier, source=source, raw_data=sanitized_raw, parsed_data=parsed if isinstance(parsed, dict) else {"value": parsed}, collection_method=method, confidence=max(0.0, min(1.0, confidence)), target_device=target_device, command_or_query=command, request_type=source.value, evidence_hash=evidence_hash)

    def _provided_items(self, prefix: str, source: EvidenceSource, values: Iterable[Mapping[str, Any]], method: CollectionMethod, confidence: float) -> list[EvidenceItem]:
        """Convert mappings into deterministic evidence items."""
        return [self._item(f"{prefix}:{index}", source, value, value, method, confidence, str(value.get("target_device", "")), str(value.get("command", value.get("command_or_query", "")))) for index, value in enumerate(values, start=1)]
