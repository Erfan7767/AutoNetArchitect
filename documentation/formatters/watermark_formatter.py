"""Watermark helpers."""
from __future__ import annotations

from enum import Enum


class Watermark(str, Enum):
    """Supported document watermark labels."""

    DRAFT = "DRAFT"
    CONFIDENTIAL = "CONFIDENTIAL"
    NONE = ""


class WatermarkFormatter:
    """Validate and expose watermark labels."""

    def format(self, value: Watermark | str = Watermark.DRAFT) -> str:
        """Return the selected watermark."""
        return Watermark(value).value
