"""Resolve documentation sections from supplied source artifacts only."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .doc_models import DocumentSection, DocumentSection as Section, DocumentType, ResolvedData, ResolvedSectionData, SectionStatus
from .doc_section_registry import DocumentSectionRegistry


class DocDataResolver:
    """Resolve source records without inventing missing design or operational facts."""

    def resolve(self, *, document_type: DocumentType | str, artifacts: Mapping[str, Any], registry: DocumentSectionRegistry, sections_override: Sequence[str] | None = None) -> ResolvedData:
        """Resolve all selected sections and mark missing records as PENDING."""
        selected = DocumentType(document_type)
        sections = list(registry.get(selected))
        if sections_override is not None:
            allowed = set(sections_override)
            sections = [section for section in sections if section.section_id in allowed]
        resolved: list[ResolvedSectionData] = []
        for section in sections:
            content, source_key = self._find_content(section, artifacts)
            if section.status == SectionStatus.NOT_APPLICABLE:
                resolved.append(ResolvedSectionData(section=section, content=content, has_content=False, status=SectionStatus.NOT_APPLICABLE, pending_reason=section.pending_reason, source_artifacts=[source_key] if content is not None else [], source_timestamps=self._timestamps(artifacts)))
            elif content is None or content == "" or content == [] or content == {}:
                resolved.append(ResolvedSectionData(section=section, content=None, has_content=False, status=SectionStatus.PENDING, pending_reason=f"PENDING: {section.data_source} artifact not supplied", source_artifacts=[], source_timestamps=[], assumptions=[f"missing:{section.data_source}"]))
            else:
                resolved.append(ResolvedSectionData(section=section, content=content, has_content=True, status=SectionStatus.COMPLETE, source_artifacts=[source_key], source_timestamps=self._timestamps(artifacts)))
        pending = [item.section.section_id for item in resolved if item.status == SectionStatus.PENDING]
        complete = [item for item in resolved if item.status == SectionStatus.COMPLETE]
        mandatory = [item for item in resolved if item.section.mandatory and item.status not in {SectionStatus.NOT_APPLICABLE}]
        mandatory_complete = all(item.has_content for item in mandatory)
        score = round((len(complete) + sum(1 for item in resolved if item.status == SectionStatus.NOT_APPLICABLE)) * 100 / len(resolved), 2) if resolved else 0.0
        sot = self._basis(artifacts, "sot_basis")
        evidence = [str(item) for item in artifacts.get("evidence_basis", [])] if isinstance(artifacts.get("evidence_basis", []), Sequence) and not isinstance(artifacts.get("evidence_basis", []), (str, bytes)) else []
        assumptions = [f"PENDING: {item}" for item in pending]
        return ResolvedData(document_type=selected, sections=resolved, completeness_score=score, mandatory_sections_complete=mandatory_complete, pending_sections=pending, stale_sections=[str(item) for item in artifacts.get("stale_sections", [])], sot_basis=sot, evidence_basis=evidence, assumptions=assumptions)

    @staticmethod
    def _find_content(section: DocumentSection, artifacts: Mapping[str, Any]) -> tuple[Any, str]:
        """Find exact source key or section-specific content."""
        sections = artifacts.get("sections")
        if isinstance(sections, Mapping) and section.section_id in sections:
            return sections[section.section_id], f"sections.{section.section_id}"
        if section.data_source in artifacts:
            return artifacts[section.data_source], section.data_source
        source_artifacts = artifacts.get("source_artifacts")
        if isinstance(source_artifacts, Mapping) and section.data_source in source_artifacts:
            return source_artifacts[section.data_source], f"source_artifacts.{section.data_source}"
        return None, section.data_source

    @staticmethod
    def _basis(artifacts: Mapping[str, Any], key: str) -> dict[str, str]:
        """Read a mapping basis without generating record IDs."""
        value = artifacts.get(key, {})
        return {str(item_key): str(item_value) for item_key, item_value in value.items()} if isinstance(value, Mapping) else {}

    @staticmethod
    def _timestamps(artifacts: Mapping[str, Any]) -> list[str]:
        """Read supplied source timestamps only."""
        values = artifacts.get("source_timestamps", [])
        return [str(item) for item in values] if isinstance(values, Sequence) and not isinstance(values, (str, bytes)) else []
