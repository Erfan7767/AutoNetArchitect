# AutoNetArchitect V1 Testing Guide

## Testing philosophy

Testing V1 verifies behavior, boundaries, persistence, governance, secret safety, and failure handling. A passing test demonstrates the tested behavior under the stated fixture and evidence conditions; it does not prove every vendor, topology, field condition, or production environment.

The repository uses custom importlib-based runners in the current release workflow. This keeps the test layer runnable in a minimal Python installation even when the optional `pytest` dependency is not installed. `pytest`, `httpx`, `ruff`, `build`, and `wheel` remain in `requirements-dev.txt` for developer convenience and future migration.

Always run from the repository root with the project on `PYTHONPATH`:

```bash
cd /home/ubuntu/AutoNetArchitect
export PYTHONPATH=/home/ubuntu/AutoNetArchitect
```

## Test families

| Family | Coverage |
|---|---|
| Unit | Models, registries, policies, designers, generators, services, gates, and reporters |
| Integration | Full pipeline, brownfield flow, cross-vendor behavior, and serialization roundtrips |
| E2E | CLI/UI/API-adjacent user flows and governed deployment flow |
| Performance | Large projects, JSON loading, config generation, report generation, and memory behavior |
| Chaos | Disconnects, partial responses, malformed responses, timeouts, flaky links, permission failures, corruption, and missing dependencies |
| Release hardening | Packaging metadata, dependency separation, docs, Docker safety, env example, entry points, and release files |

Fixtures are stored under `tests/fixtures`. Golden projects are evidence fixtures for repeatability, not claims that the same result is correct for every real network.

## Running individual custom runners

The root-level runners are executable Python files. Examples:

```bash
python3 /home/ubuntu/run_final_tests.py
python3 /home/ubuntu/run_api_tests.py
python3 /home/ubuntu/run_cli_tests.py
python3 /home/ubuntu/run_ui_tests.py
python3 /home/ubuntu/run_orchestrators_tests.py
python3 /home/ubuntu/run_release_tests.py
```

The full regression command is:

```bash
set -e
for runner in /home/ubuntu/run_*_tests.py; do
  PYTHONPATH=/home/ubuntu/AutoNetArchitect python3 "$runner"
done
```

The runner output must be preserved with the release evidence. A failed or skipped family is a release issue unless its exclusion and risk acceptance are explicitly documented by the release owner.

## Compile and static checks

Compile all Python files without creating a package artifact:

```bash
PYTHONPATH=/home/ubuntu/AutoNetArchitect python3 -m compileall -q .
```

Check release-facing text files for forbidden implementation markers:

```bash
grep -RInE 'forbidden-marker-token' \\
  docs requirements*.txt setup.py Makefile .env.example || echo 'clean'
```

The repository policy also requires that Python files contain real behavior, type hints for public interfaces, and docstrings for modules and public methods. A token scan is not a substitute for code review; it is a release guardrail.

## Regression acceptance

A release candidate must satisfy all repository runners, compile successfully, and succeed in the release-hardening tests. Tests involving external integrations must remain explicit about whether they are mocks, lab adapters, read-only discovery, or real evidence. A mocked response cannot be labeled as a production observation.

For deployment-related tests, assert the policy boundary: dry-run is allowed where the fixture permits it, approval is required for real execution, backups are mandatory, unresolved HumanSuppliedMandatory inputs block execution, and post-deployment verification and rollback references are preserved.

For report and export tests, assert that the output declares timestamp and SoT basis and contains no secret values. For compliance tests, assert technical assessment scope and limitations rather than certification or readiness claims.

## Release manifest and reproducibility

The release manifest enumerates the release documentation, packaging files, release-hardening tests, and checksum file inputs. Generate checksums only after the files have been finalized:

```bash
{
  find docs -type f | sort
  printf '%s\\n' requirements.txt requirements-dev.txt requirements-optional.txt \\
    setup.py pyproject.toml MANIFEST.in Dockerfile docker-compose.yml Makefile \\
    README.md CHANGELOG.md LICENSE .env.example
  printf '%s\\n' tests/test_release_hardening.py
} > RELEASE_MANIFEST.txt
xargs sha256sum < RELEASE_MANIFEST.txt > RELEASE_SHA256SUMS.txt
```

The merged archive must exclude `__pycache__` directories and `.pyc` files. Record the archive test output and checksum values as part of the release evidence.

## Benchmarking boundary

Benchmarking must identify the scenario corpus, baseline source, sample size, scoring policy, evidence IDs, and limitations. The scoring layer may report measured acceptance, failure, false-positive, false-negative, abstention, reliability, and rollback metrics. It must not state that the system is equivalent to an engineer or safe for all production environments based on a limited sample.

## Containerized test execution

The repository also provides `docker-compose.test.yml` for a reproducible containerized pytest run. The test service is built from `Dockerfile.dev`, mounts the source tree read-only at `/workspace`, stores pytest cache and temporary coverage output in named volumes, runs `tests/` with the declared coverage configuration, and stops on the first failure. It uses `AUTONET_RUNTIME_MODE=test` and does not claim `AUTONET_DATABASE_PATH=:memory:` isolation because that variable is not consumed by the V1 persistence implementation.

Run the service with:

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```

The service is a validation path only. Its successful result does not authorize production deployment, replace human review, or establish a universal production-safety claim.
