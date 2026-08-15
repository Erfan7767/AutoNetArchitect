# Module development

A new module should begin with a clear responsibility, input contract, output contract, source-of-truth basis, failure states, evidence status, and human checkpoint requirements. The module should use existing foundation models and domain boundaries rather than introducing a parallel representation.

## Implementation sequence

Start with the model and policy boundary, then implement deterministic behavior, then add tests for normal, blocked, unknown, ambiguous, and failure outcomes. Connect the module to its orchestrator or service only after the isolated contract is stable. Add an integration test when the module changes a workflow stage, Source of Truth record, audit trail, approval path, or exported artifact.

## Required boundaries

A designer or generator must not invent non-inferable values. A configuration generator must check capability and feature evidence before emitting commands. A deployment module must call the governance and review gates, require backups and verification, and preserve rollback scope. An exporter must redact secrets and declare timestamp and SoT basis. An operations module must remain read-only for high-risk production changes unless an approved policy explicitly authorizes the action.

## Compatibility and deprecation

Prefer additive changes. When a schema or public response changes, provide a migration or versioned contract and update fixtures. Keep legacy custom runners working unless the release notes explain the transition. Dependency changes belong in the correct manifest group and require security and package-build checks.
