# AutoNetArchitect

## نظرة عامة / Overview

**AutoNetArchitect** هو نظام محلي أولاً لأتمتة هندسة الشبكات تحت إشراف مهندس بشري. يجمع المتطلبات، يحافظ على الأدلة والافتراضات، ينشئ قرارات وتصاميم قابلة للتتبع، يربط اختيار المعدات بقدرات موثقة، يولد artifacts محمية بالـ capability guards، ويفرض المراجعة والاعتماد والنسخ الاحتياطي والتحقق قبل مسارات النشر.

AutoNetArchitect is a **local-first, engineer-supervised network engineering automation system**. It captures requirements, preserves assumptions and evidence, produces traceable design decisions, selects equipment using capability evidence, generates guarded configuration artifacts, and enforces review, approval, backup, verification, and rollback controls around deployment paths.

> **V1 definition:** The system may automate bounded engineering preparation and evidence organization. It does not become an autonomous network operator, does not replace accountable engineering authority, and does not make a universal production-safety claim.

## النطاق المدعوم في V1 / Supported V1 scope

| Area | V1 behavior |
|---|---|
| Workflow | Questionnaire, requirements, design, equipment/BOM, config preparation, deployment preparation, operations, compliance assessment, and reports |
| Vendors | Aruba, Cisco, Fortinet, Huawei, Juniper, MikroTik, and Palo Alto within recorded capability and generator boundaries |
| Persistence | Local-first project state with atomic save, checksums, migrations, and Source of Truth domains |
| Governance | Human accountability, supervised checkpoints, expert overrides, mandatory review, no-go outcomes, and audit trail |
| Deployment | Dry-run and governed execution paths with backup, verification, rollback, and approval controls |
| Operations | Read-only monitoring, discovery, drift, health, backup, maintenance governance, troubleshooting, and incident support |
| Compliance | Technical control assessment with explicit scope, evidence basis, limitations, and no certification claim |
| Reporting | Bilingual-capable reports, redacted exports, diagrams, as-built and handover artifacts, with timestamp and SoT basis |

The supported vendor list does not mean that every model, software version, license, command, feature, or transport is supported. Exact capability evidence remains required. MikroTik and other preview-only contexts remain outside an unqualified production path where the applicable policy marks them as preview-only.

## الحدود المقصودة / Explicit boundaries

The following are intentionally outside an unqualified V1 claim:

- autonomous production operation or autonomous approval;
- full-fidelity protocol emulation or a complete live digital twin without corresponding evidence;
- certification, regulatory readiness, legal advice, clinical validity, or safety certification;
- equivalence to a human engineer;
- multi-tenant isolation or hosted enterprise identity;
- invented ASNs, public prefixes, IP allocations, port numbers, floor dimensions, power values, device facts, or site conditions;
- unsupported vendor/model/version commands or guessed configuration substitutions;
- auto-remediation of high-risk production drift without explicit approval.

If a mandatory input is not inferable, it remains a `HumanSuppliedMandatory` item. If evidence is insufficient, the system may abstain, downgrade confidence, require review, or return a formal no-go outcome.

## Production readiness definition / تعريف الجاهزية الإنتاجية

A project is **not production-ready merely because an artifact was generated, a simulation completed, or a test passed**. A production-readiness decision requires a bounded project scope and applicable evidence for all of the following:

1. requirements are complete for the execution path, with contradictions and HumanSuppliedMandatory gaps resolved;
2. unsupported scope and field-feasibility boundaries have been reviewed;
3. design decisions, assumptions, alternatives, evidence, and SoT records are traceable;
4. equipment, licensing, BOM, optics, physical, power, and service dependencies are reviewed;
5. configuration artifacts pass exact capability and feature guards, formal/intent checks where inputs permit, and secret-safety checks;
6. mandatory human review, approval, separation of duties, and no-go checkpoints are resolved;
7. deployment preparation contains a backup reference, verification plan, rollback scope, maintenance window where required, and authorized change reference;
8. post-deployment acceptance and operational evidence are defined and recorded.

The resulting status must declare its proof status, evidence basis, assumptions affecting the result, unresolved items, and SoT basis. It is valid only for the assessed scope and time. The system does not generalize that status to another network or organization.

## بدء سريع / Quick start

### CLI

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .

autonet --help
```

The CLI is local-first and writes to its own local context. Use the project-specific help before invoking a workflow stage:

```bash
autonet system info --help
autonet project --help
autonet workflow --help
```

### API

```bash
export AUTONET_API_ROOT="$HOME/.autonetarchitect-api"
export AUTONET_API_HOST=127.0.0.1
export AUTONET_API_PORT=8000
PYTHONPATH="$PWD" python -m api.server
```

Open `http://127.0.0.1:8000/docs` for the local OpenAPI document. Health endpoints are available under `/api/v1/health`. The default API binding is loopback. If the binding is changed, the operator must provide the surrounding network, identity, TLS, secrets, logging, and access controls; changing the bind address alone is not a production-readiness decision.

### Docker

```bash
cp .env.example .env
docker compose up --build
```

The compose baseline binds the API to localhost, stores state in a persistent named volume, runs as a non-root user, drops capabilities, enables `no-new-privileges`, and uses a read-only container filesystem. Review `docs/DEPLOYMENT_GUIDE.md` and `docs/SECURITY_GUIDE.md` before using the container beyond a controlled local environment.

## الأدلة والمراجعة / Evidence and review

Every non-trivial decision should retain a `DecisionRecord` or equivalent provenance, assumptions, evidence references, confidence, and Source of Truth basis. Reports declare their generation timestamp and SoT domain. Exports redact secret values. Review and approval are different from execution authority; the governance layer records those distinctions.

Benchmarking is the only layer that may issue maturity-oriented measurements, and it must bound them by corpus, sample size, scoring policy, and evidence. A measured rate is not a promise about an unmeasured environment.

## التوثيق / Documentation

| Document | Purpose |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Layer map, data flow, SoT domains, boundaries, and extension rules |
| [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) | Local installation, API/CLI startup, Docker, state, backup, and deployment gates |
| [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) | Versioned endpoints, authentication, rate limiting, errors, and response semantics |
| [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md) | Custom runners, test families, regression, compile, and release evidence |
| [`docs/SECURITY_GUIDE.md`](docs/SECURITY_GUIDE.md) | Secrets, RBAC, audit, exports, deployment boundaries, and container baseline |
| [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | Code standards, provenance, no-fake-data rules, tests, and PR review |

## الترخيص / License

This release is distributed under the MIT License. See [`LICENSE`](LICENSE). The license does not change the system's technical limitations, human approval requirements, or evidence boundaries.
