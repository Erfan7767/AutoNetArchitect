"""Estimate generation budgets for source artifacts."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class BudgetRecommendation:
    """Token estimate and recommended prompt count."""
    estimated_tokens: int
    model_limit: int
    recommended_sub_prompts: int

class TokenBudgetEstimator:
    """Deterministic estimator based on artifact type and complexity."""
    RATIOS = {'model': 7.0, 'designer': 6.0, 'test': 5.0, 'config': 3.0, 'template': 4.0, 'docs': 4.0}
    COMPLEXITY = {'simple': 1.0, 'medium': 1.25, 'complex': 1.6, 'very_complex': 2.1}
    LIMITS = {'claude_sonnet_output_limit': 12000, 'claude_opus_output_limit': 16000, 'gpt4_output_limit': 12000}

    def estimate_file(self, file_type: str, complexity_class: str, estimated_lines: int) -> int:
        """Estimate output tokens for one file."""
        if file_type not in self.RATIOS or complexity_class not in self.COMPLEXITY:
            raise ValueError('unknown file type or complexity class')
        return round(estimated_lines * self.RATIOS[file_type] * self.COMPLEXITY[complexity_class])

    def recommend(self, estimates: list[int], target_model: str = 'claude_sonnet_output_limit') -> BudgetRecommendation:
        """Recommend the number of prompts under a model output limit."""
        if target_model not in self.LIMITS: raise ValueError('unknown target model')
        total, limit = sum(estimates), self.LIMITS[target_model]
        return BudgetRecommendation(total, limit, max(1, (total + limit - 1) // limit))
