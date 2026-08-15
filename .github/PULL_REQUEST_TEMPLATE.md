## Summary / الملخص

## Description

<!-- What does this PR do? Describe the user-visible, operational, governance, or developer-facing outcome. -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Test addition
- [ ] CI/CD or build configuration
- [ ] Security, governance, or compliance boundary change

## Phase/Module Affected

<!-- Which phase(s), package(s), layer(s), workflow stage(s), or release artifacts does this affect? -->

## Safety and scope / السلامة والنطاق

- [ ] The change preserves the local-single-user V1 scope and does not introduce unsupported multi-tenant behavior.
- [ ] No ASNs, public prefixes, site dimensions, device facts, port values, credentials, or other HumanSuppliedMandatory values were invented.
- [ ] Unsupported, ambiguous, insufficient-evidence, preview-only, and production-blocked paths remain explicit.
- [ ] Production-affecting behavior retains review, approval, backup, verification, rollback, audit, and no-go controls.
- [ ] Deployment, firmware, remote-destructive, secret, and configuration-generation paths do not bypass policy gates.
- [ ] Compliance and maturity language remains bounded by declared evidence, scope, and proof status.
- [ ] No `pass`, `TODO`, `FIXME`, `HACK`, placeholder, ellipsis, or fake success assertion was introduced in implementation files.

## Provenance and accountability / التتبع والمسؤولية

- [ ] DecisionRecords, assumptions, evidence references, Source of Truth domain, and override provenance remain traceable where applicable.
- [ ] Human review, approval, execution authority, separation-of-duties, and escalation requirements remain enforceable where applicable.
- [ ] Expert overrides preserve the machine decision, human decision, rationale, scope, impact, timestamp, actor, and revalidation requirement.
- [ ] Secrets and raw secret values are absent from source, tests, logs, fixtures, reports, examples, and generated artifacts.

## Checklist

- [ ] Code follows project coding standards.
- [ ] All tests pass (`make test`).
- [ ] Linting passes (`make lint`).
- [ ] Type checking passes (`make typecheck`).
- [ ] Security scan passes (`make security`).
- [ ] Aggregate mandatory checks pass (`make check-all`) when applicable.
- [ ] No `pass`, `TODO`, or placeholder statements were introduced.
- [ ] All public functions, classes, and methods have type hints and useful docstrings.
- [ ] New tests were added for new or changed functionality.
- [ ] Documentation was updated if behavior, scope, configuration, or operational procedure changed.
- [ ] No secrets were committed.
- [ ] DecisionRecords were added for design decisions.
- [ ] Assumptions were registered if applicable.
- [ ] CI required checks are enabled and no mandatory check is knowingly skipped.
- [ ] Release manifests, checksums, and archives were regenerated when release-facing files changed.

## Testing / التحقق

<!-- List exact commands and concise results. Include relevant custom runners, fixtures, and environment boundaries. -->

```text
make test
make lint
make typecheck
make security
python3 -m compileall -q .
python3 /home/ubuntu/run_<relevant>_tests.py
python3 /home/ubuntu/run_release_tests.py
```

- [ ] Unit tests cover normal, blocked, ambiguous, and failure outcomes where applicable.
- [ ] Integration or E2E tests cover cross-layer behavior when applicable.
- [ ] Failure, timeout, rollback, and ambiguity paths are covered where the change affects them.
- [ ] Test evidence states whether integrations are mocked, lab-only, read-only discovery, or real evidence.
- [ ] Coverage and quality results do not overstate production readiness or engineer equivalence.

## Screenshots (if applicable)

<!-- Add screenshots for UI changes. Redact secrets, credentials, internal addresses, and sensitive topology details. -->

## Release impact / أثر الإصدار

<!-- Describe migrations, dependency changes, workflow changes, Docker changes, generated artifacts, rollback considerations, and bounded follow-up work. -->
