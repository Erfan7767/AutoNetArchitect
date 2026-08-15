"""Unified diff creation, patch application, and conflict detection."""
from __future__ import annotations
import difflib

class DiffPatchManager:
    """Manage text revisions without external dependencies."""
    def create_diff(self, old: str, new: str, filename: str = 'file') -> str:
        """Create a unified diff."""
        return ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), filename, filename))
    def apply_patch(self, original: str, old: str, new: str) -> str:
        """Apply an exact replacement and reject ambiguous patches."""
        if original.count(old) != 1: raise ValueError('patch context is missing or ambiguous')
        return original.replace(old, new, 1)
    def detect_conflict(self, base: str, left: str, right: str) -> bool:
        """Detect incompatible concurrent edits."""
        return left != base and right != base and left != right
