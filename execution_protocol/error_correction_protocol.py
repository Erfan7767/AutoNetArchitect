"""Error taxonomy and correction prompt generation."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ErrorRule:
    """Correction policy for one error category."""
    correction_strategy: str
    context_needed_for_correction: tuple[str, ...]
    prompt_template_for_correction: str

class ErrorCorrectionProtocol:
    """Provide deterministic correction rules."""
    RULES = {k: ErrorRule(s, ('error output', 'affected file', 'relevant contract'), f'Correct {k} in {{file}} using {{context}}.') for k, s in {'syntax_error':'regenerate_file','import_error':'patch_file','type_mismatch':'regenerate_function','missing_implementation':'regenerate_file','wrong_vendor_command':'patch_file','test_failure':'patch_file','logic_error':'regenerate_function'}.items()}
    def rule_for(self, error_type: str) -> ErrorRule:
        """Return a rule for a known error type."""
        if error_type not in self.RULES: raise KeyError(error_type)
        return self.RULES[error_type]
