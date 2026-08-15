"""Build compact context handoff summaries."""
from __future__ import annotations
from typing import Any

class ContextHandoffManager:
    """Preserve critical state under target model limits."""
    def summarize(self, state: dict[str, Any], max_tokens: int) -> str:
        """Serialize prioritized state and truncate only at a safe boundary."""
        sections = ['completed_phases', 'current_file_registry', 'pending_items', 'known_issues', 'active_assumptions', 'active_decisions']
        text = '\n'.join(f'{key}: {state.get(key, [])}' for key in sections)
        limit = max_tokens * 4
        return text if len(text) <= limit else text[:limit - 15] + '\n[summary truncated]'
