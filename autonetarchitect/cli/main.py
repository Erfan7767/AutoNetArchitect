"""Module invocation wrapper for the AutoNetArchitect CLI."""

from __future__ import annotations

from cli.main import VERSION, cli

__all__ = ["VERSION", "cli"]


if __name__ == "__main__":
    cli()
