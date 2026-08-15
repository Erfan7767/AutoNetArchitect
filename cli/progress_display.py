"""Terminal progress helpers for long-running CLI commands."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterable, Iterator


@dataclass
class ProgressDisplay:
    """Small progress adapter suitable for TTY and piped output."""

    enabled: bool = True
    verbose: bool = False

    def update(self, label: str, current: int, total: int | None = None) -> None:
        """Emit one progress update when enabled."""
        if not self.enabled:
            return
        suffix = f" {current}/{total}" if total is not None else f" {current}"
        print(f"{label}{suffix}")

    def steps(self, label: str, items: Iterable[Any]) -> list[Any]:
        """Iterate items and report completion counts."""
        materialized = list(items)
        results: list[Any] = []
        total = len(materialized)
        for index, item in enumerate(materialized, start=1):
            results.append(item)
            self.update(label, index, total)
        return results

    @contextmanager
    def spinner(self, label: str) -> Iterator[None]:
        """Emit start/end markers around a blocking adapter call."""
        if self.enabled:
            print(f"{label} ...")
        try:
            yield
        finally:
            if self.enabled:
                print(f"{label} complete")
