"""Predict generated file size and overflow risk."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SizePrediction:
    """Predicted lines, tokens, and whether output exceeds a limit."""
    lines: int
    tokens: int
    exceeds_limit: bool

class OutputSizePredictor:
    """Simple calibrated line/token predictor."""
    def predict(self, prompt_tokens: int, requested_files: int, avg_lines: int, limit: int) -> SizePrediction:
        """Predict output from prompt and file parameters."""
        lines = max(0, requested_files) * max(0, avg_lines)
        tokens = round(lines * 5 + prompt_tokens * 0.15)
        return SizePrediction(lines, tokens, tokens > limit)
