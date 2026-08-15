# Dependency injection container

The project contains infrastructure helpers for dependency construction and health checks. Dependency injection is used to make persistence, audit, secret, governance, and orchestrator boundaries explicit and testable. A test may inject an isolated local state root or a deterministic adapter; it must not inject a fake production fact and label it as discovered evidence.

## Rules

The container should construct dependencies at the application boundary and inject them inward. Core modules should depend on interfaces or narrow service contracts where the repository already defines them. CLI, API, and UI adapters request orchestrator dependencies rather than constructing design or deployment algorithms themselves.

Optional integrations are imported lazily. Importing the core package must not require Streamlit, WeasyPrint, plotting libraries, external credentials, or a vendor SDK that is not declared for the selected path. When an optional integration is absent, the system should return an explicit unavailable or not-verifiable result rather than silently changing the design.

Test fixtures should inject temporary persistence and redaction-aware audit sinks. Secret stores should remain isolated from assertions and artifacts. Dependency construction must not bypass authentication, RBAC, review gates, approval gates, or Source of Truth transitions.
