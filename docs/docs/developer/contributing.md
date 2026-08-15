# Contributing

Contributions must preserve the supervised, evidence-bounded, local-first scope. A pull request that weakens approval gates, invents field data, exposes secrets, or broadens a claim without evidence must be rejected even if its local checks succeed.

Every public Python interface should carry type hints and a useful docstring. New behavior requires focused tests for normal, blocked, ambiguous, and failure outcomes where applicable. Adapters should call orchestrators or services; business logic must not be duplicated in CLI, API, or UI pages.

## Pull request evidence

The pull request description should state affected layers, safety boundaries, test commands, dependency changes, migration impact, and release impact. Redact credentials and sensitive topology details. Changes touching secrets, authentication, audit, governance, deployment, firmware, compliance, or production-facing claims require maintainers with the corresponding ownership rule.

Branch protection should require the CI `required-checks` job, the security `security-required` job, and dependency review where the repository settings support it. GitLab users should protect the default branch with the complete `gate` stage.
