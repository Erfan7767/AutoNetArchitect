# Changelog

All notable changes to AutoNetArchitect are recorded in this file. The project follows a bounded release policy: an implemented feature is not automatically a production-safety claim.

## [0.1.0] — Initial V1 release

### Added

- Local-first project persistence with atomic saves, checksums, migrations, and Source of Truth domains.
- Requirements, design, equipment, configuration, services, operations, verification, reporting, compliance, and documentation layers.
- Supported vendor boundaries for Aruba, Cisco, Fortinet, Huawei, Juniper, MikroTik, and Palo Alto, subject to exact capability and policy evidence.
- Secret management, PKI inventory, secure logging and redaction, local authentication, RBAC, sessions, and audit trail support.
- Discovery and reconciliation paths with explicit unknown and ambiguous outcomes.
- Lab adapters and a logical simulator that remain validation paths rather than production change-control substitutes.
- Deployment preparation and execution gates for dry-run, approval, backup, verification, rollback, and audit integration.
- Firmware, monitoring, drift, health, backup, maintenance, troubleshooting, incident, and traffic-analysis foundations.
- Formal verification and intent-validation taxonomy separating verified, partially verified, not verifiable with current inputs, and failed outcomes.
- Enterprise, banking, hospital/clinical, and university/campus domain packs with constrained cross-pack governance.
- Human accountability, supervised workflow mode, expert override provenance, mandatory review checkpoints, no-go enforcement, discrepancy memory, review console, benchmarking, and orchestrators.
- V1 CLI, versioned FastAPI API, framework-neutral UI shell, package metadata, dependency separation, Docker baseline, compose configuration, release documentation, and release-hardening tests.

### Scope notes

- V1 is local-single-user and does not provide multi-tenant isolation.
- Compliance outputs are technical assessments only and do not provide certification or regulatory readiness.
- Benchmark outputs must remain bounded by corpus, sample size, scoring policy, and evidence.
- Generated artifacts do not establish production safety without explicit proof status and human governance evidence.
