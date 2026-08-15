# CI/CD policy

## Primary and secondary providers

GitHub Actions is the primary supported CI provider. GitLab CI is maintained as a secondary mapping for installations that mirror the repository. Both providers run the same conceptual checks: linting, formatting, type checking, unit/integration/E2E/chaos testing, security and dependency auditing, coverage, package build validation, documentation build, and container smoke verification.

The provider configuration uses current major action tags and Dependabot updates. Repository administrators should review action major-version compatibility with their runner fleet, especially when using self-hosted runners. Action tags are not a substitute for organization-level runner hardening or branch protection.

## Mandatory checks

The GitHub `required-checks` and `security-required` jobs are aggregate gates. Branch protection should require both aggregate jobs and dependency review before merge. The aggregate jobs fail when an upstream job fails or is cancelled. The GitLab `gate` stage has the same intent and should be required by default-branch protection.

A pull request must not merge because an individual check was skipped, made informational, or marked as allowed failure. Exceptions require an explicit repository-owner decision recorded outside the code change and must not silently remove the underlying safety requirement.

## Release permissions

Tag pushes build and validate the source distribution and wheel. GitHub Release creation is limited to version tags and write permissions. PyPI publication uses trusted publishing and is opt-in through repository configuration or an explicit workflow input. Container publication is also opt-in and requires package write permission. Documentation publication is limited to GitHub Pages permissions and the configured environment.

No CI workflow receives network-device credentials or executes a production network change. Container smoke tests invoke the CLI help boundary. Real network deployment remains subject to AutoNetArchitect governance and human approval, not repository automation.

## Security checks

The security workflow runs dependency auditing, Bandit, secret scanning, and CodeQL. Dependency review blocks vulnerable runtime additions on pull requests according to the configured severity threshold. A finding must be resolved, bounded with authoritative evidence and an approved policy decision, or the merge must remain blocked.

## Pre-commit policy

The pre-commit configuration runs repository hygiene checks, YAML/JSON/TOML validation, large-file and private-key detection, branch protection for `main`, Python AST validation, debug-statement detection, Ruff lint/format checks, mypy, and Bandit. The configured revisions track current stable tool releases rather than the older revisions in historical snippets.

The no-pass hook uses AST analysis and excludes tests because tests may intentionally exercise blocked or unavailable branches. The maintenance-marker hook reports `TODO`, `FIXME`, `HACK`, and `XXX` findings with verbose output but remains warning-only by policy. Production code must still avoid incomplete implementation markers; warning-only behavior is used so historical review can occur without silently converting a warning into a false quality claim.

Ruff is restricted to the maintained compatibility namespace and CI-owned scripts/tests declared in `pyproject.toml`; this prevents mass reformatting of the pre-existing legacy tree. The broader custom regression suite remains the behavioral guard for those modules. Mypy now enables strict return, generic, equality, unreachable-code, untyped-call, incomplete-definition, and implicit-optional checks, with optional-library import exemptions. Its `files = autonetarchitect` and `follow_imports = skip` boundary is explicit: the validated result covers the installable compatibility namespace and does not claim strict typing for every historical implementation module.

The local workflow files are configuration, not proof that a repository has enabled branch protection, CodeQL storage, Pages, trusted publishing, or an organizational security policy. Those controls must be configured in the hosting platform.

## Local Makefile parity

The repository Makefile mirrors the main local CI boundaries without claiming that a local command replaces hosted branch protection. `make check-all` runs the compact blocking set of lint, strict typing, unit/CI contract tests, and mandatory security scans. `make docs` performs the documentation link check and strict MkDocs build, while `make build` validates the source distribution and wheel.

The `run-api`, `run-ui`, and `run-cli` targets are local V1 entry-point checks. The API target uses the implemented `api.server` module, the UI target starts the optional shell only, and the CLI target runs help without requiring an authenticated operation. Database migration is deliberately separate as an explicit operator command and is never invoked by `check-all` or repository automation. Docker targets are local validation/development paths; they do not receive network-device credentials or perform production deployment.
