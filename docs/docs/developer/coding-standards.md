# Coding standards

## Python and formatting

Use Python 3.11 syntax and Pydantic v2 conventions. Public interfaces require type hints and docstrings. Ruff is the formatter and primary lint tool. The CI configuration runs `ruff check . --config pyproject.toml` and `ruff format --check . --config pyproject.toml`; local changes should use the same commands.

Prefer explicit enums and domain exceptions at policy boundaries. Keep optional imports lazy. Avoid hidden global state, uncontrolled network calls, and broad exception swallowing. Keep adapters thin and keep safety policy at the service or orchestrator boundary.

## Engineering data

Do not fabricate ASNs, public prefixes, site facts, model capabilities, physical measurements, power values, or credentials. Use human-mandatory fields, explicit assumptions, evidence records, unresolved items, or no-decision outcomes. Synthetic fixtures must be clearly labeled and must not be reported as operational observations.

## Provenance and security

Non-trivial decisions retain DecisionRecord or equivalent provenance, assumptions, evidence basis, confidence or proof status, and Source of Truth domain. Configuration artifacts use secret references. Raw secret values must not appear in tests, logs, reports, exports, issue reports, CI artifacts, or documentation.

## Quality policy

A green formatting or type check is one quality signal. It does not prove network correctness or production readiness. Deployment-related changes must retain review, approval, backup, verification, rollback, audit, and no-go behavior.
