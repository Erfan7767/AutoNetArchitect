"""Console entry point for AutoNetArchitect."""
from __future__ import annotations

from .app import VERSION, cli

__all__ = ["VERSION", "cli"]


if __name__ == "__main__":
    cli()
