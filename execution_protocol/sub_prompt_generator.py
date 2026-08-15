"""Generate standardized prompts from sub-prompt metadata."""
from __future__ import annotations
from .phase_subdivider import SubPrompt

class SubPromptGenerator:
    """Render self-contained execution prompts."""
    def generate(self, sub_prompt: SubPrompt, objective: str, constraints: list[str] | None = None) -> str:
        """Generate a complete prompt for one sub-prompt."""
        rules = constraints or ["write complete files", "preserve public contracts", "include type hints and docstrings"]
        return (f"Phase {sub_prompt.parent_phase_id}, sub-prompt {sub_prompt.sub_prompt_id}.\n"
                f"Objective: {objective}\nFiles: {', '.join(sub_prompt.files_included)}\n"
                f"Context: {', '.join(sub_prompt.context_requirements)}\n"
                f"Constraints: {'; '.join(rules)}\n"
                "Return every requested file in full and report validation results.")
