# AutoNetArchitect

AutoNetArchitect V1 is a local-first, engineer-supervised network engineering system. It organizes requirements, evidence, assumptions, design decisions, equipment capability checks, guarded configuration artifacts, governed deployment preparation, read-only operations, technical compliance assessment, and reports.

> A generated artifact, simulated result, or successful test is not by itself proof of production safety.

The documentation is divided into installation, architecture, developer, and API references. Read the production-readiness boundaries in the root README before interpreting workflow outcomes, and begin with [Quickstart](getting-started/quickstart.md).

## V1 operating boundaries

The current release is local-single-user. It does not provide multi-tenant isolation, universal vendor/model support, autonomous approval, engineer-equivalence, regulatory certification, or a complete protocol emulator. Missing non-inferable inputs remain human-mandatory. Unsupported or ambiguous paths are recorded, downgraded, blocked, or returned as a no-decision result.

## Quality and release evidence

Every pull request is expected to run linting, formatting, type checking, tests, security and dependency scanning, documentation build, package verification, and container smoke verification. Branch protection must require the repository's mandatory CI and security gate checks before merging.
