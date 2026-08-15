"""Tests for interactive CLI adapters."""
from __future__ import annotations

from collections import deque

from cli.interactive_mode import InteractiveMode


def test_interactive_questionnaire_collects_required_and_optional_values():
    answers = deque(["HQ", "skip", "10"])
    mode = InteractiveMode(input_fn=lambda _prompt: answers.popleft(), output_fn=lambda _message: None)
    result = mode.questionnaire([{"name": "site", "prompt": "Site"}, {"name": "note", "optional": True}, {"name": "count"}])
    assert result == {"site": "HQ", "count": "10"}


def test_interactive_review_and_deployment_steps_are_controlled():
    answers = deque(["accept", "modify", "new-value"])
    output: list[str] = []
    mode = InteractiveMode(input_fn=lambda _prompt: answers.popleft(), output_fn=output.append)
    decisions = mode.review_decisions([{"decision_id": "D1", "summary": "Use design A"}, {"decision_id": "D2", "summary": "Use design B"}])
    accepted = mode.deployment_steps(["backup", "execute"], confirm=lambda prompt: "backup" in prompt)
    assert decisions[0].value == "accept"
    assert decisions[1].value == "modify:new-value"
    assert accepted == ["backup"]
