"""Interactive CLI prompts that remain separate from workflow business logic."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


@dataclass(frozen=True)
class InteractiveAnswer:
    """One interactive answer with a field name and value."""

    name: str
    value: str
    skipped: bool = False


class InteractiveMode:
    """Collect user input while delegating validation and action to callers."""

    def __init__(self, *, input_fn: InputFunction = input, output_fn: OutputFunction = print) -> None:
        """Create an interactive adapter with injectable terminal functions."""
        self.input_fn = input_fn
        self.output_fn = output_fn

    def questionnaire(self, questions: Iterable[Mapping[str, Any]]) -> dict[str, str]:
        """Prompt for questions one at a time, honoring optional skips."""
        answers: dict[str, str] = {}
        question_list = list(questions)
        for index, question in enumerate(question_list, start=1):
            name = str(question.get("name", f"field_{index}"))
            prompt = str(question.get("prompt", name))
            optional = bool(question.get("optional", False))
            suffix = " [optional; enter skip to omit]" if optional else ""
            value = self.input_fn(f"{index}/{len(question_list)} {prompt}{suffix}: ")
            if optional and value.strip().lower() in {"skip", ""}:
                continue
            if not value.strip() and not optional:
                raise ValueError(f"required answer missing: {name}")
            answers[name] = value
        return answers

    def review_decisions(self, decisions: Iterable[Mapping[str, Any]]) -> list[InteractiveAnswer]:
        """Ask accept/reject/modify for each externally supplied decision."""
        results: list[InteractiveAnswer] = []
        for decision in decisions:
            decision_id = str(decision.get("decision_id", "decision"))
            summary = str(decision.get("summary", ""))
            self.output_fn(f"Decision {decision_id}: {summary}")
            action = self.input_fn("Choose accept, reject, modify, or skip: ").strip().lower()
            if action not in {"accept", "reject", "modify", "skip"}:
                raise ValueError("decision action must be accept, reject, modify, or skip")
            if action == "modify":
                action = f"modify:{self.input_fn('New value: ')}"
            results.append(InteractiveAnswer(decision_id, action, action == "skip"))
        return results

    def deployment_steps(self, steps: Iterable[str], *, confirm: Callable[[str], bool]) -> list[str]:
        """Confirm each externally described deployment step."""
        accepted: list[str] = []
        for step in steps:
            label = str(step)
            if confirm(f"Proceed with deployment step '{label}'?"):
                accepted.append(label)
            else:
                break
        return accepted
