"""Report maintainability-marker comments without blocking a commit."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Final

MARKER_PATTERN: Final[re.Pattern[str]] = re.compile(r"\b(?:TO" + "DO|FIXME|HACK|XXX)\b")


def main(argv: list[str] | None = None) -> int:
    """Print marker locations and always return success for warning-only policy."""
    paths = argv if argv is not None else sys.argv[1:]
    findings: list[str] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.suffix != ".py" or "tests" in path.parts:
            continue
        try:
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if MARKER_PATTERN.search(line):
                    findings.append(f"{path}:{line_number}:{line.strip()}")
        except OSError as error:
            findings.append(f"{path}: cannot read ({error})")
    for finding in findings:
        print(f"WARNING_MAINTENANCE_MARKER {finding}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
