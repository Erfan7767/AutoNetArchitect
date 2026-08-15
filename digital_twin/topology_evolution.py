"""Temporal topology evolution tracking for Digital Twin views."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class TopologyVersion:
    """One timestamped topology representation."""

    version_id: str
    timestamp: str
    source_kind: str
    nodes: tuple[dict[str, Any], ...]
    links: tuple[dict[str, Any], ...]
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize one topology version."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class TopologyChange:
    """One detected change between topology versions."""

    from_version: str
    to_version: str
    added_nodes: tuple[str, ...] = ()
    removed_nodes: tuple[str, ...] = ()
    changed_nodes: tuple[str, ...] = ()
    added_links: tuple[str, ...] = ()
    removed_links: tuple[str, ...] = ()
    changed_links: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize topology change details."""
        return asdict(self) | {"added_nodes": list(self.added_nodes), "removed_nodes": list(self.removed_nodes), "changed_nodes": list(self.changed_nodes), "added_links": list(self.added_links), "removed_links": list(self.removed_links), "changed_links": list(self.changed_links), "evidence_ids": list(self.evidence_ids)}


class TopologyEvolution:
    """Track explicit topology versions and derive deterministic diffs."""

    def __init__(self) -> None:
        """Create an empty evolution ledger."""
        self._versions: list[TopologyVersion] = []

    def record(self, timestamp: str, source_kind: str, nodes: Sequence[Mapping[str, Any]], links: Sequence[Mapping[str, Any]], evidence_ids: Sequence[str] = ()) -> TopologyVersion:
        """Record a topology version without inventing absent nodes or links."""
        if not timestamp or not source_kind:
            raise ValueError("timestamp and source_kind are required")
        normalized_nodes = tuple(dict(node) for node in nodes if isinstance(node, Mapping) and node.get("id", node.get("name")))
        normalized_links = tuple(dict(link) for link in links if isinstance(link, Mapping) and link.get("id", link.get("link_id")))
        if not normalized_nodes and not normalized_links:
            raise ValueError("topology version requires explicit nodes or links")
        payload = {"timestamp": timestamp, "source_kind": source_kind, "nodes": normalized_nodes, "links": normalized_links, "evidence_ids": tuple(evidence_ids)}
        version_id = f"topology:{hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode('utf-8')).hexdigest()[:16]}"
        if any(version.version_id == version_id for version in self._versions):
            raise ValueError("topology version already recorded")
        version = TopologyVersion(version_id, timestamp, source_kind, normalized_nodes, normalized_links, tuple(dict.fromkeys(str(item) for item in evidence_ids)))
        self._versions.append(version)
        self._versions.sort(key=lambda item: (item.timestamp, item.version_id))
        return version

    def versions(self) -> tuple[TopologyVersion, ...]:
        """Return topology versions in temporal order."""
        return tuple(self._versions)

    def changes(self) -> tuple[TopologyChange, ...]:
        """Return diffs between adjacent recorded versions."""
        return tuple(self._diff(left, right) for left, right in zip(self._versions, self._versions[1:]))

    @staticmethod
    def _diff(left: TopologyVersion, right: TopologyVersion) -> TopologyChange:
        """Compare normalized node/link records by explicit IDs."""
        left_nodes = {str(item.get("id", item.get("name"))): item for item in left.nodes}
        right_nodes = {str(item.get("id", item.get("name"))): item for item in right.nodes}
        left_links = {str(item.get("id", item.get("link_id"))): item for item in left.links}
        right_links = {str(item.get("id", item.get("link_id"))): item for item in right.links}
        return TopologyChange(left.version_id, right.version_id, tuple(sorted(set(right_nodes) - set(left_nodes))), tuple(sorted(set(left_nodes) - set(right_nodes))), tuple(sorted(key for key in set(left_nodes) & set(right_nodes) if left_nodes[key] != right_nodes[key])), tuple(sorted(set(right_links) - set(left_links))), tuple(sorted(set(left_links) - set(right_links))), tuple(sorted(key for key in set(left_links) & set(right_links) if left_links[key] != right_links[key])), tuple(sorted(set(left.evidence_ids + right.evidence_ids))))
