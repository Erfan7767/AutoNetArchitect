PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
PACKAGE ?= autonetarchitect
API_HOST ?= 127.0.0.1
API_PORT ?= 8000
DB_PATH ?=
PYTEST ?= $(PYTHON) -m pytest
RUFF ?= $(PYTHON) -m ruff
MYPY ?= $(PYTHON) -m mypy

.PHONY: help install install-dev install-optional install-hooks lint format format-check typecheck test test-unit test-integration test-e2e test-chaos test-all test-parallel pytest-all final-tests regression compile security coverage docs docs-serve quality pre-commit build docker docker-build docker-dev docker-build-dev docker-test docker-cli-smoke docker-up docker-down docker-up-dev docker-down-dev docker-test-up docker-test-down run-api run-ui run-cli db-migrate check-all clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

install-dev: ## Install runtime and development dependencies
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .

install-optional: ## Install optional rendering, UI, and analysis integrations
	$(PIP) install -r requirements-optional.txt

install-hooks: ## Install pre-commit and commit-message hooks
	$(PYTHON) -m pre_commit install
	$(PYTHON) -m pre_commit install --hook-type commit-msg

lint: ## Run Ruff lint checks
	$(RUFF) check . --config pyproject.toml
	$(RUFF) format --check . --config pyproject.toml

format: ## Apply Ruff lint fixes and formatting
	$(RUFF) check . --fix --config pyproject.toml
	$(RUFF) format . --config pyproject.toml

format-check: ## Check Ruff formatting without changing files
	$(RUFF) format --check . --config pyproject.toml

typecheck: ## Run strict mypy policy on the declared compatibility namespace
	$(MYPY) autonetarchitect/ --config-file mypy.ini

test: test-all ## Run all supported pytest families

test-unit: ## Run unit and CI contract tests with configured coverage
	PYTHONPATH=. AUTONET_RUNTIME_MODE=test $(PYTEST) tests/unit/ tests/ci/ -v --tb=short --cov=autonetarchitect --cov-config=coverage_config/.coveragerc --cov-report=term-missing -x

test-integration: ## Run integration tests
	PYTHONPATH=. AUTONET_RUNTIME_MODE=test $(PYTEST) tests/integration/ -v --tb=short -x

test-e2e: ## Run end-to-end tests
	PYTHONPATH=. AUTONET_RUNTIME_MODE=test $(PYTEST) tests/e2e/ -v --tb=short --timeout=300 -x

test-chaos: ## Run controlled chaos tests
	PYTHONPATH=. AUTONET_RUNTIME_MODE=test $(PYTEST) tests/chaos/ -v --tb=short -x

test-all: ## Run unit, CI, integration, end-to-end, and chaos families
	$(MAKE) test-unit
	$(MAKE) test-integration
	$(MAKE) test-e2e
	$(MAKE) test-chaos

test-parallel: ## Run unit and CI tests in parallel when pytest-xdist is installed
	PYTHONPATH=. AUTONET_RUNTIME_MODE=test $(PYTEST) tests/unit/ tests/ci/ -v --tb=short -n auto --cov=autonetarchitect --cov-config=coverage_config/.coveragerc

pytest-all: test-all ## Compatibility alias for the standard pytest aggregate

# The repository retains custom importlib runners for the full historical suite.
final-tests: ## Run the final comprehensive custom test layer
	PYTHONPATH=. $(PYTHON) /home/ubuntu/run_final_tests.py

regression: ## Run every historical custom test runner
	@set -e; for runner in /home/ubuntu/run_*_tests.py; do PYTHONPATH=. $(PYTHON) $$runner; done

compile: ## Compile Python sources without executing workflows
	PYTHONPATH=. $(PYTHON) -m compileall -q .

security: ## Run mandatory Bandit and pip-audit plus supplemental Safety scan
	AUTONET_SECURITY_PYTHON=$(PYTHON) bash scripts/run_security_scan.sh

coverage: ## Generate configured branch coverage, HTML, and XML reports
	PYTHONPATH=. AUTONET_RUNTIME_MODE=test ./scripts/generate_coverage.sh
	@echo "Coverage report: htmlcov/index.html"

quality: compile lint format-check typecheck ## Run local code-quality checks

docs: ## Build strict documentation
	$(PYTHON) scripts/check_docs_links.py
	$(PYTHON) -m mkdocs build --strict --config-file docs/mkdocs.yml

docs-serve: ## Serve documentation locally
	$(PYTHON) -m mkdocs serve --config-file docs/mkdocs.yml

pre-commit: ## Run all configured pre-commit hooks
	$(PYTHON) -m pre_commit run --all-files

build: ## Build and validate sdist and wheel
	rm -rf build dist *.egg-info
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*

docker: docker-build ## Build the release Docker image

docker-build: ## Build the release Docker image
	docker build -t $(PACKAGE):0.1.0 .

docker-dev: docker-build-dev ## Build the development Docker image

docker-build-dev: ## Build the development Docker image
	docker build -f Dockerfile.dev -t $(PACKAGE):dev .

docker-test: ## Run test-only Docker Compose environment
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test

docker-cli-smoke: ## Run an unauthenticated CLI startup smoke check in the release image
	docker build -t $(PACKAGE):ci .
	docker run --rm $(PACKAGE):ci autonet --help

docker-up: ## Start the release Compose API service
	docker compose up --build

docker-down: ## Stop the release Compose API service
	docker compose down

docker-up-dev: ## Start the development Compose service
	docker compose -f docker-compose.dev.yml up --build

docker-down-dev: ## Stop the development Compose service
	docker compose -f docker-compose.dev.yml down

docker-test-up: docker-test ## Compatibility alias for test-only Compose

docker-test-down: ## Remove test-only Compose containers and volumes
	docker compose -f docker-compose.test.yml down --volumes

run-api: ## Run the FastAPI API on the configured local host and port
	AUTONET_API_HOST=$(API_HOST) AUTONET_API_PORT=$(API_PORT) PYTHONPATH=. $(PYTHON) -m api.server

run-ui: ## Run the optional Streamlit shell when optional dependencies are installed
	streamlit run ui/app.py

run-cli: ## Run an unauthenticated CLI startup/help check
	PYTHONPATH=. $(PYTHON) -m autonetarchitect --help

run-system-info: ## Run authenticated local system information command
	PYTHONPATH=. $(PYTHON) -m autonetarchitect system info

db-migrate: ## Run an explicit local database migration with optional DB_PATH
	AUTONET_RUNTIME_MODE=maintenance PYTHONPATH=. $(PYTHON) -m autonetarchitect system db migrate $(if $(DB_PATH),--path $(DB_PATH),)

check-all: lint typecheck test-unit security ## Run all mandatory local checks

clean: ## Clean build, test, coverage, and Python cache artifacts
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache .tox .nox htmlcov coverage.xml coverage-data bandit-report.json pip-audit.json safety-report.json
