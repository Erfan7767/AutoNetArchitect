"""Question definitions and bilingual labels."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field
class LocalizedText(BaseModel):
    """English and Arabic text pair."""
    en: str
    ar: str
class Question(BaseModel):
    """Validated question contract."""
    question_id: str
    text: LocalizedText
    field: str
    value_type: str
    mandatory_for: list[str] = Field(default_factory=list)
    human_supplied_mandatory: bool = False
    choices: list[str] = Field(default_factory=list)
    default: Any = None
class QuestionAnswer(BaseModel):
    """Answer to one question."""
    question_id: str
    value: Any = None
    source: str = "human"
    confirmed: bool = True
