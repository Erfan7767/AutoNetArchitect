"""Compatibility entry point for legacy setuptools callers.

Project metadata and dependencies are maintained in pyproject.toml. This file
exists only for tools that still invoke ``python setup.py`` during migration.
"""
from __future__ import annotations

from setuptools import setup


if __name__ == "__main__":
    setup()
