# AutoNetArchitect V1 Contributing Guide

## Contribution contract

Contributions must preserve AutoNetArchitect's supervised, evidence-bounded, local-first scope. The project is a network engineering automation system, not an autonomous replacement for accountable engineers. A pull request that weakens an approval gate, invents field data, exposes secrets, or broadens a claim without evidence is not acceptable even if its checks succeed.

Every public module, class, function, and method must have a useful docstring and type hints. New behavior must be covered by focused tests and, when it crosses layers, an integration test. Prefer the standard library and existing project boundaries before adding a dependency.

## No-fake-data rules

Do not fabricate ASNs, public prefixes, IP addresses that should be human supplied, port numbers, floor dimensions, cable lengths, power values, device facts, vendor capabilities, certification evidence, or field conditions. If a value is not inferable from authoritative evidence, represent it as `HumanSuppliedMandatory`, an explicit assumption, an unresolved item, or a no-decision result.

A test fixture may use clearly labeled synthetic values when the test needs them, but it must not present them as discovered production facts. Golden projects are repeatability fixtures. Their names, comments, and evidence metadata must make that boundary clear.

## Provenance and governance

Every non-trivial component must preserve `DecisionRecord` and `Assumption` or the equivalent project provenance model. A new decision path must identify its source-of-truth domain, evidence basis, confidence, alternatives or abstention, and human checkpoint requirements.

Production-affecting behavior must integrate with governance, audit, review control, supervised mode, deployment safety, and rollback policy. An override is never a silent mutation. It must preserve the machine decision, human decision, rationale, scope, impact, timestamp, actor, and revalidation requirement.

## Coding and repository standards

Use Python 3.11+ syntax and Pydantic v2 conventions. Use explicit enums for controlled states and avoid accepting arbitrary strings where a policy boundary depends on a finite set. Raise domain-specific exceptions with actionable messages. Keep import-time behavior safe: optional integrations must be lazy, and importing the core package must not require Streamlit, WeasyPrint, plotting libraries, or external credentials.

Keep adapters thin. CLI, API, and UI code should validate transport input and call orchestrators or services; business logic belongs in the corresponding layer. Configuration generators must run capability and feature guards before emitting a command. Unsupported or ambiguous paths must be recorded rather than approximated.

## Tests and checks

Run the relevant custom runner while developing, then run the complete regression before opening a pull request:

```bash
export PYTHONPATH=/home/ubuntu/AutoNetArchitect
python3 /home/ubuntu/run_<layer>_tests.py
set -e
for runner in /home/ubuntu/run_*_tests.py; do python3 "$runner"; done
python3 -m compileall -q .
```

Release-facing changes must also run the release-hardening runner, forbidden-token check, package build, manifest generation, checksum validation, and archive integrity test. Never use `assert True` as a test substitute. Tests should verify meaningful outputs, state transitions, exceptions, secret redaction, or policy boundaries.

## Documentation and claim review

Update the relevant documentation when behavior or scope changes. Documentation must distinguish technical assessment from certification, simulation evidence from formal verification evidence, and lab validation from production acceptance. Benchmarking claims must include the corpus, sample size, metric definition, evidence IDs, and limitations.

Avoid words such as “fully autonomous,” “certified,” “engineer-equivalent,” or “production-safe” unless the exact claim is supported by the appropriate evidence and bounded scope. The default documentation stance is to state what is implemented, what is measured, what is unknown, and what requires human review.

## Pull request process

A pull request should explain the problem, affected layers, data and policy boundaries, test commands, and any migration or release impact. Include representative structured outputs where useful, but redact secrets and sensitive network details. Reviewers should check the code, tests, documentation, provenance, no-go behavior, and failure paths rather than accepting a happy-path demonstration alone.

At least one reviewer must examine changes that affect secrets, authentication, audit, deployment, firmware, compliance, governance, or production-facing claims. Changes to a release artifact require regenerated checksums and an updated changelog entry.

## Review checklist

| Area | Contributor evidence |
|---|---|
| Behavior | Focused tests cover normal, blocked, ambiguous, and failure outcomes |
| Safety | High-risk paths retain review, approval, backup, verification, and rollback gates |
| Data | No fabricated mandatory inputs or unsupported vendor/model facts |
| Provenance | Decisions, assumptions, evidence, SoT, audit, and override history remain traceable |
| Security | No secrets in source, tests, logs, reports, examples, or archive |
| Scope | V1 boundaries and no-claims language remain accurate |
| Release | Compile, regression, package, manifest, checksum, and archive checks are complete |

## Local files and Git ignore boundaries

The repository `.gitignore` excludes generated Python/build/test outputs, local vault material, keys and certificates, SQLite files, project data, caches, backups, logs, IDE state, and optional frontend dependencies. `.env.example` and `.env.test` remain intentionally reviewable; they must contain names and test-safe defaults only. Release manifests, checksum files, source files, and documentation are not ignored by this policy. Git ignore rules do not remove files that were already tracked, so any accidental secret committed in the past requires separate revocation, history remediation, and incident handling.

## Pull request evidence

Use `.github/PULL_REQUEST_TEMPLATE.md` for every change. Complete the change type and affected phase/module, state the exact validation commands and results, and identify whether evidence comes from mocks, a lab, read-only discovery, or a real operational observation. Changes affecting design, deployment, security, compliance, governance, secrets, or production-facing claims must preserve DecisionRecords, assumptions, Source of Truth references, human checkpoints, and bounded claim language. A checked box is not evidence by itself; the PR description must provide the corresponding result or explain why a check is not applicable.

## Code ownership

`.github/CODEOWNERS` assigns a global core owner and specialized owners for foundation, design, configuration, security, operations, and CI/CD paths. The patterns are repository-relative and use the actual V1 layout; a team handle must be created in GitHub before branch protection can enforce required ownership review. CODEOWNERS ownership identifies the required review group, but it does not replace the PR checklist, human accountability, separation-of-duties, security review, or deployment approval policy.

## Dependency update ownership

Dependabot proposes weekly updates for Python packages, GitHub Actions, and Docker image references. Python updates are reviewed by `autonet-core-team`, while GitHub Actions and Docker updates are reviewed by `autonet-devops-team`. Pip major-version updates are intentionally ignored for automatic proposal flow and require an explicit engineering review. Dependency review, security scanning, compatibility testing, and release evidence remain mandatory for accepted updates.
