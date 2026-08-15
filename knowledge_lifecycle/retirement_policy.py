"""Retirement rules for permanently unusable knowledge."""
from __future__ import annotations
class RetirementPolicy:
    """Retire items after defined terminal conditions."""
    def retire(self, item: object, reason: str) -> object:
        """Mark an item retired and preserve the reason."""
        if getattr(item, "publication_state", "") not in {"deprecated", "blocked"}: raise ValueError("only deprecated or blocked items may retire")
        item.publication_state = "retired"; item.status = "retired"; item.validation_errors.append(reason); return item
