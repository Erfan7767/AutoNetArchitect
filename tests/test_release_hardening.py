"""Release-hardening tests for the AutoNetArchitect V1 source distribution."""

from __future__ import annotations

import importlib
import re
import tomllib
import unittest
from pathlib import Path
from typing import Final


ROOT: Final[Path] = Path(__file__).resolve().parents[1]
REQUIRED_RUNTIME: Final[set[str]] = {
    "click",
    "fastapi",
    "uvicorn",
    "pydantic",
    "jinja2",
    "pyyaml",
    "reportlab",
    "openpyxl",
    "pillow",
}
REQUIRED_DOCS: Final[dict[str, tuple[str, ...]]] = {
    "ARCHITECTURE.md": (
        "# AutoNetArchitect V1 Architecture",
        "## Layered model",
        "## Source of Truth domains",
        "## Security boundaries",
        "## Evidence and claim discipline",
    ),
    "DEPLOYMENT_GUIDE.md": (
        "# AutoNetArchitect V1 Deployment Guide",
        "## Installation from a source checkout",
        "## Local API",
        "## Docker baseline",
        "## Network deployment readiness",
    ),
    "API_REFERENCE.md": (
        "# AutoNetArchitect V1 API Reference",
        "## API contract",
        "## Authentication",
        "## Project endpoints",
        "## Deployment endpoints",
        "## Rate limiting",
    ),
    "TESTING_GUIDE.md": (
        "# AutoNetArchitect V1 Testing Guide",
        "## Testing philosophy",
        "## Test families",
        "## Running individual custom runners",
        "## Release manifest and reproducibility",
    ),
    "SECURITY_GUIDE.md": (
        "# AutoNetArchitect V1 Security Guide",
        "## Security posture",
        "## Secret handling",
        "## Authentication and RBAC",
        "## Deployment boundaries",
    ),
    "CONTRIBUTING.md": (
        "# AutoNetArchitect V1 Contributing Guide",
        "## Contribution contract",
        "## No-fake-data rules",
        "## Provenance and governance",
        "## Pull request process",
    ),
}
FORBIDDEN_SECRET_ASSIGNMENT: Final[re.Pattern[str]] = re.compile(
    r"(?im)^\s*(?:password|passwd|secret|token|api[_-]?key|private[_-]?key)\s*[:=]"
)


class ReleaseHardeningTests(unittest.TestCase):
    """Verify that release-facing files preserve the V1 contract."""

    def test_pyproject_has_required_metadata_and_entry_points(self) -> None:
        """Require build metadata, runtime dependencies, and both public entry points."""
        metadata_path = ROOT / "pyproject.toml"
        with metadata_path.open("rb") as handle:
            document = tomllib.load(handle)
        project = document["project"]
        self.assertEqual(project["name"], "autonetarchitect")
        self.assertEqual(project["version"], "0.1.0")
        self.assertGreaterEqual(len(project["description"]), 40)
        self.assertEqual(project["requires-python"], ">=3.11")
        self.assertEqual(project["license"]["file"], "LICENSE")
        self.assertTrue(REQUIRED_RUNTIME.issubset(self._normalise_dependencies(project["dependencies"])))
        scripts = project["scripts"]
        self.assertEqual(scripts["autonet"], "autonetarchitect.cli.main:cli")
        self.assertEqual(scripts["autonet-api"], "api.server:main")
        self.assertIn("dev", project["optional-dependencies"])
        self.assertIn("optional", project["optional-dependencies"])

    def test_requirements_have_no_secret_values(self) -> None:
        """Ensure runtime and optional dependency manifests contain package names only."""
        for filename in ("requirements.txt", "requirements-dev.txt", "requirements-optional.txt"):
            content = (ROOT / filename).read_text(encoding="utf-8")
            self.assertNotRegex(content, FORBIDDEN_SECRET_ASSIGNMENT)
            self.assertNotRegex(content, r"(?i)(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]+PRIVATE KEY-----)")
            for line in content.splitlines():
                stripped = line.strip()
                self.assertFalse(stripped.startswith("http://"), stripped)
                self.assertFalse(stripped.startswith("https://"), stripped)

    def test_env_example_contains_only_non_secret_local_defaults(self) -> None:
        """Ensure the environment example documents names without credential material."""
        content = (ROOT / ".env.example").read_text(encoding="utf-8")
        for key in ("AUTONET_API_ROOT", "AUTONET_API_HOST", "AUTONET_API_PORT", "PYTHONPATH"):
            if key == "PYTHONPATH":
                self.assertIn(key, content)
        self.assertNotRegex(content, FORBIDDEN_SECRET_ASSIGNMENT)
        self.assertNotRegex(content, r"(?i)(password|passwd|api[_-]?key|private[_-]?key|bearer|token\s*=)")
        self.assertNotRegex(content, r"-----BEGIN [A-Z ]+PRIVATE KEY-----")
        self.assertIn("local-single-user", content)

    def test_entry_points_are_importable(self) -> None:
        """Import the modules behind the installed console entry points."""
        cli_module = importlib.import_module("autonetarchitect.cli.main")
        api_module = importlib.import_module("api.server")
        self.assertTrue(callable(getattr(cli_module, "cli", None)))
        self.assertTrue(callable(getattr(api_module, "main", None)))
        self.assertTrue(hasattr(api_module, "app"))

    def test_docker_files_have_safe_baseline(self) -> None:
        """Ensure container files use non-root and persistent state without baked secrets."""
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("FROM python:3.11-slim", dockerfile)
        self.assertIn("USER autonet", dockerfile)
        self.assertIn("AUTONET_API_ROOT", dockerfile)
        self.assertIn("VOLUME", dockerfile)
        self.assertIn('CMD ["python", "-m", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]', dockerfile)
        self.assertNotRegex(dockerfile, FORBIDDEN_SECRET_ASSIGNMENT)
        self.assertNotRegex(compose, FORBIDDEN_SECRET_ASSIGNMENT)
        self.assertIn("autonet_state", compose)
        self.assertIn("read_only: true", compose)
        self.assertIn("cap_drop:", compose)
        self.assertIn("no-new-privileges:true", compose)
        self.assertIn('127.0.0.1:8000:8000', compose)

    def test_documentation_files_exist_and_have_required_sections(self) -> None:
        """Require the six release guides and their critical boundary sections."""
        docs_dir = ROOT / "docs"
        for filename, sections in REQUIRED_DOCS.items():
            path = docs_dir / filename
            self.assertTrue(path.is_file(), filename)
            content = path.read_text(encoding="utf-8")
            self.assertGreater(len(content), 600, filename)
            for section in sections:
                self.assertIn(section, content, f"{filename}: {section}")
            self.assertNotIn("TODO", content)
            self.assertNotIn("placeholder", content.lower())

    def test_release_root_files_are_present(self) -> None:
        """Require all named V1 release files before archive creation."""
        filenames = (
            "pyproject.toml",
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-optional.txt",
            "setup.py",
            "MANIFEST.in",
            "Dockerfile",
            "docker-compose.yml",
            "Makefile",
            "README.md",
            "CHANGELOG.md",
            "LICENSE",
            ".env.example",
        )
        for filename in filenames:
            self.assertTrue((ROOT / filename).is_file(), filename)

    @staticmethod
    def _normalise_dependencies(dependencies: list[str]) -> set[str]:
        """Return lower-case package names from PEP 508 dependency strings."""
        names: set[str] = set()
        for dependency in dependencies:
            names.add(re.split(r"[<>=!~;\[]", dependency, maxsplit=1)[0].strip().lower())
        return names


if __name__ == "__main__":
    unittest.main(verbosity=2)
