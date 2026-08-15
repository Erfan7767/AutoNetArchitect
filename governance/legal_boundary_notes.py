"""Non-legal boundary notes for human accountability governance."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner


class LegalBoundaryNote(BaseModel):
    """A bounded note preventing technical automation from being mistaken for legal authority."""

    model_config = ConfigDict(extra="forbid")

    note_id: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    statement_en: str = Field(min_length=1)
    statement_ar: str = Field(min_length=1)
    limitation: str = Field(min_length=1)
    required_human_action: str = Field(min_length=1)
    jurisdiction_scope: str = "not supplied"
    source_basis: tuple[str, ...] = ()
    not_legal_advice: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LegalBoundaryRegistry(BaseDesigner):
    """Registry of boundary notes surfaced in governance reports."""

    def __init__(self, notes: Iterable[LegalBoundaryNote] | None = None) -> None:
        """Initialize the registry with conservative default notes."""
        super().__init__("LegalBoundaryRegistry")
        self._notes: dict[str, LegalBoundaryNote] = {note.note_id: note for note in self.default_notes()}
        for note in notes or ():
            self._notes[note.note_id] = note
        self.record_decision("legal_boundary_defaults", "technical_only", "the system records governance boundaries but does not provide legal advice or regulatory acceptance")

    @staticmethod
    def default_notes() -> tuple[LegalBoundaryNote, ...]:
        """Return default boundary notes."""
        return (
            LegalBoundaryNote(note_id="legal-001", subject="technical_assessment", statement_en="A technical assessment or compliance report is not a certification, legal opinion, or readiness determination.", statement_ar="التقييم التقني أو تقرير الامتثال ليس شهادة أو رأياً قانونياً أو حكماً بالجاهزية.", limitation="Authoritative scope, evidence sufficiency, and regulatory interpretation remain human responsibilities.", required_human_action="Obtain qualified legal, regulatory, and audit review where applicable.", source_basis=("governance.technical_only",)),
            LegalBoundaryNote(note_id="legal-002", subject="signoff", statement_en="A system-recorded sign-off does not replace the accountable person's professional or organizational responsibility.", statement_ar="تسجيل الاعتماد في النظام لا يحل محل المسؤولية المهنية أو التنظيمية للشخص المعتمد.", limitation="The artifact proves that a checkpoint was recorded, not that the decision was substantively correct.", required_human_action="Review the evidence, scope, assumptions, and consequences before approval.", source_basis=("governance.human_accountability",)),
            LegalBoundaryNote(note_id="legal-003", subject="emergency_change", statement_en="An emergency override is an operational governance exception, not a legal or regulatory waiver.", statement_ar="التجاوز الطارئ استثناء تشغيلي للحوكمة وليس إعفاءً قانونياً أو تنظيمياً.", limitation="Post-implementation review and applicable external obligations remain in force.", required_human_action="Escalate to the responsible incident, legal, and compliance authorities as required.", source_basis=("governance.emergency_change",)),
        )

    def register(self, note: LegalBoundaryNote) -> LegalBoundaryNote:
        """Register or replace a boundary note."""
        self._notes[note.note_id] = note
        self.record_decision(f"legal_note:{note.note_id}", "registered", "boundary note was explicitly registered with human action and limitation")
        return note

    def get(self, note_id: str) -> LegalBoundaryNote:
        """Return one boundary note."""
        return self._notes[note_id]

    def all(self) -> tuple[LegalBoundaryNote, ...]:
        """Return notes in stable identifier order."""
        return tuple(self._notes[key] for key in sorted(self._notes))

    def for_subject(self, subject: str) -> tuple[LegalBoundaryNote, ...]:
        """Return notes matching a subject."""
        return tuple(note for note in self.all() if note.subject == subject)
