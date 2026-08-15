"""Validate local Markdown links used by the MkDocs documentation site."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final
from urllib.parse import unquote, urlsplit

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DOCS_ROOT: Final[Path] = PROJECT_ROOT / "docs" / "docs"
MARKDOWN_LINK: Final[re.Pattern[str]] = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def local_target(source: Path, href: str) -> Path | None:
    """Resolve an internal Markdown href, returning None for external or anchor-only links."""
    value = href.strip().strip("<>")
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or value.startswith("#"):
        return None
    raw_path = unquote(parsed.path)
    if not raw_path:
        return None
    candidate = (source.parent / raw_path).resolve()
    if candidate.is_dir():
        candidate = candidate / "index.md"
    if candidate.suffix == "":
        markdown_candidate = candidate.with_suffix(".md")
        if markdown_candidate.exists():
            candidate = markdown_candidate
    return candidate


def find_broken_links() -> list[str]:
    """Return deterministic descriptions for missing local Markdown targets."""
    broken: list[str] = []
    for source in sorted(DOCS_ROOT.rglob("*.md")):
        content = source.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(content):
            href = match.group(1)
            target = local_target(source, href)
            if target is not None and not target.exists():
                broken.append(f"{source.relative_to(PROJECT_ROOT)} -> {href}")
    return broken


def main() -> int:
    """Print local link status and return a non-zero status for broken links."""
    broken = find_broken_links()
    if broken:
        for item in broken:
            print(f"BROKEN {item}")
        return 1
    print(f"documentation links: checked={sum(1 for _ in DOCS_ROOT.rglob('*.md'))} markdown files, broken=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
