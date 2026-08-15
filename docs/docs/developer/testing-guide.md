# Testing guide

The repository contains more than one test execution path. The custom importlib runners preserve the historical layer-by-layer regression suite, while pytest discovers the structured `tests/unit`, `tests/integration`, `tests/e2e`, and `tests/chaos` families used by CI.

## Local commands

```bash
export PYTHONPATH="$PWD"
make test
make regression
make coverage
make lint
make format-check
make typecheck
make security
make docs
```

The coverage job measures the installable compatibility namespace `autonetarchitect` with branch coverage and a 70 percent minimum. Reports omit tests, migrations, package initializers, CLI completions, and Streamlit page adapters according to `coverage_config/.coveragerc`. The report displays covered files rather than hiding them, writes `coverage.xml`, and creates an HTML report titled `AutoNetArchitect Coverage Report` under `htmlcov/`. This is a deliberately declared coverage scope, not a claim that every network-engineering module has been exercised by that metric. Historical custom runners provide additional layer coverage.

## Test design

Unit tests should verify models, policies, gates, serialization, redaction, and deterministic transformations. Integration tests should verify cross-layer contracts and Source of Truth transitions. E2E tests should verify user-visible workflow boundaries. Chaos tests should exercise controlled disconnects, malformed responses, corrupted state, timeouts, and missing dependencies.

Deployment tests must assert that dry-run is distinct from real execution, approvals and backups are mandatory for the applicable path, unresolved HumanSuppliedMandatory items block execution, and verification and rollback references survive the result. Compliance tests must assert technical scope and limitations instead of certification language.

## CI artifact discipline

Coverage files, security reports, packages, and documentation sites are CI evidence artifacts. They should be retained according to repository policy and must not contain raw secrets or uncontrolled production data. A test result is evidence for the tested fixture and version; it is not a universal production claim.

## Tox environments

`tox -e py311` and `tox -e py312` run the unit coverage command for each supported interpreter when that interpreter is available. `tox -e integration` and `tox -e e2e` use the all-dependencies extra. The `lint`, `typecheck`, `security`, `docs`, and `build` environments reuse the repository Ruff, mypy, Bandit, pip-audit, documentation, and packaging policies. Missing local interpreters are skipped by tox; a hosted matrix remains responsible for providing both Python versions when the corresponding checks are required.

The security environment calls the repository security script so pip-audit and Bandit remain mandatory while the current authenticated Safety CLI path stays supplemental and non-interactive. This avoids a local tox run hanging on a login prompt and does not bypass the mandatory dependency audit.

## Makefile command semantics

The Makefile is the supported local command surface for the repository. `make test-unit` runs the unit suite together with CI contract tests and uses the repository coverage configuration; `make test-all` adds integration, E2E, and controlled chaos families. `make test-parallel` is an opt-in acceleration path and requires the declared `pytest-xdist` development dependency.

`make check-all` is the compact mandatory gate for local development: Ruff linting, strict mypy, the unit and CI contract suite, and mandatory security scanning. `make security` delegates to the repository security script so Bandit and pip-audit remain blocking while the authenticated Safety path remains supplemental and non-interactive.

The API target starts the implemented `api.server` module. The UI target starts the optional Streamlit shell at `ui/app.py`; it does not add business logic or bypass supervised workflow gates. `make run-cli` performs an unauthenticated CLI startup/help check, while `make run-system-info` is an explicit authenticated local inspection command. `make db-migrate` is an operator-invoked local persistence operation and is not part of `check-all`; an optional `DB_PATH` may be supplied, for example `make db-migrate DB_PATH=/path/to/project.db`.

Docker targets are validation and local development paths. They do not receive production credentials or execute production network changes. Documentation builds run the local link checker before strict MkDocs rendering, and `make clean` removes generated caches and reports without deleting source or evidence manifests.

## Containerized test service

`docker-compose.test.yml` provides a reproducible pytest service built from `Dockerfile.dev`. It runs the complete discovered `tests/` tree with the repository coverage configuration, stops on the first failure, and writes the XML report to the temporary test volume at `/tmp/coverage.xml`.

The source checkout is mounted read-only at `/workspace`. Pytest cache is isolated in the named `test_cache` volume, and temporary coverage/runtime files use the named `test_tmp` volume. The service runs with `AUTONET_RUNTIME_MODE=test`, warning-level logging, an explicit `/workspace` import path, and no `AUTONET_DATABASE_PATH` claim because V1 persistence does not consume that variable. The container also drops capabilities and enables `no-new-privileges`; these controls apply to the test service and do not replace test-fixture isolation or CI runner hardening.

The supported command is:

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```

If Docker is unavailable, run the equivalent host command through `make test-all` or the CI workflows. A containerized test pass is evidence for the image, source revision, fixtures, and environment tested; it is not a production-readiness certification.

## Import discovery contract

The CI import contract recursively discovers the `autonetarchitect` package and its submodules with `pkgutil.walk_packages`, then imports each discovered module through pytest parametrization. A separate core-module list verifies that the broader CLI/API/orchestrator boundaries import without requiring optional UI, rendering, plotting, or external integrations.

Importability proves only that module initialization is safe under the tested environment. It does not prove vendor capability, protocol support, production readiness, compliance, or availability of optional integrations. Optional dependencies remain tested through their explicit extras and feature-specific paths.

## Import graph and package initializer contracts

The CI layer performs a static AST analysis of top-level import statements across every discovered source package with an explicit `__init__.py`. It builds a module-level internal import graph and fails when a deterministic depth-first traversal finds a cycle. Imports nested inside functions are intentionally excluded from this import-time graph because lazy imports are an explicit V1 technique for keeping optional integrations out of core initialization; those paths remain covered by their own behavior tests.

A second contract dynamically finds every source directory containing Python files and requires an `__init__.py` in that directory. Standalone root scripts, tests, scripts, generated outputs, virtual environments, and build directories are excluded because they are not importable application packages. These checks establish structural import safety only; they do not certify runtime behavior or external integration support.
