# AutoNetArchitect V1 Architecture

## Purpose and scope

AutoNetArchitect V1 is a local-first, supervised network engineering system. Its purpose is to collect requirements, preserve evidence and assumptions, produce governed design artifacts, select equipment with capability evidence, generate guarded configuration artifacts, prepare and validate deployment paths, support read-only operations, and produce technical reports. The system is an engineering control plane and evidence organizer; it is not an autonomous network operator.

The V1 architecture deliberately separates **logical design feasibility**, **field execution feasibility**, **configuration correctness**, **deployment governance**, and **operational evidence**. A successful function call or generated artifact is not by itself proof of production safety.

## Layered model

| Layer | Primary responsibility | Release boundary |
|---|---|---|
| Questionnaire and requirements | Capture human inputs, contradictions, mandatory fields, assumptions, and requirements documents | Missing non-inferable values remain HumanSuppliedMandatory; values are not invented |
| Knowledge and evidence | Register sources, freshness, claim provenance, evidence status, and lifecycle | Claims remain bounded by evidence scope and freshness |
| Decision engine and designers | Produce traceable alternatives, decisions, assumptions, and abstentions | No decision is a valid outcome; confidence does not replace proof |
| Field reality and domain packs | Apply site constraints and sector-specific technical patterns | Sector rules cannot silently generalize to another sector |
| Equipment and config generation | Match capability/license evidence and render exact guarded commands | Unsupported features are recorded and blocked; secrets remain references |
| Persistence and Source of Truth | Store project state atomically and enforce DESIGN, DEPLOYMENT, OPERATIONAL, and COMPLIANCE domains | State transitions are versioned and checksum-protected |
| Governance and supervised mode | Require review, approval, accountability, separation of duties, and overrides with provenance | High-assurance path is supervised by default |
| Orchestrators | Primary entry points for CLI, API, and UI adapters | Enforce stage order, preconditions, SoT transitions, and audit events |
| CLI, API, and UI shell | Provide human and machine-facing adapters | No business logic, hidden execution, or secret display in adapters |
| Reports, documentation, benchmarking | Export evidence-bounded artifacts and measure quality | No certification, engineer-equivalence, or production-safe claim without measured evidence |

## Primary data flow

```text
Human inputs
    -> Questionnaire / Requirements
    -> Evidence and Knowledge Authority
    -> Decision Engine + Domain/Field Constraints
    -> Design + Equipment/BOM
    -> Config Generation + Formal/Intent Validation
    -> Review / Sign-off / No-Go Gates
    -> Deployment Preparation
    -> Approved Deployment Execution
    -> Verification / Operations / Compliance Evidence
    -> Reports, As-Built, Learning Memory, Benchmarking
```

Each transition records the workflow identifier, project identifier, actor, stage, artifact references, evidence references, assumptions, approval references, SoT record identifiers, and audit metadata. Raw passwords, private keys, tokens, and other secret values are excluded from these records.

## Source of Truth domains

The Source of Truth manager exposes four technical domains.

| Domain | Meaning | Typical evidence |
|---|---|---|
| `DESIGN` | Approved or reviewable design intent and design artifacts | requirements, decisions, design artifacts, evidence IDs |
| `DEPLOYMENT` | Deployment preparation and execution state | change reference, backup reference, deployment artifacts, verification results |
| `OPERATIONAL` | Observed or explicitly inferred live-state evidence | monitoring, discovery, drift, health, incident, and backup records |
| `COMPLIANCE` | Technical control assessment within a declared scope | control mappings, evidence basis, assessment limitations |

A stage transition cannot be treated as authoritative merely because a record exists. Where the transition requires approval, the record must have explicit approval evidence. SoT records are not a substitute for human accountability or external organizational authorization.

## Workflow ordering

The canonical V1 workflow is:

```text
questionnaire
requirements
design
equipment
config_generation
deployment_preparation
deployment_execution
operations
compliance
reports
```

Orchestrators accept only the next legal stage. A blocked result does not mutate the workflow stage. A caller cannot skip directly from design to execution, nor can a UI or API route bypass the orchestrator boundary.

## Interfaces and adapters

The CLI, FastAPI layer, and UI shell are adapters. They are responsible for parsing input, authenticating the caller, applying permission checks, formatting results, presenting approvals, and returning structured errors. They do not implement design algorithms, configuration commands, device transports, report business rules, or policy exceptions.

The V1 API is versioned under `/api/v1`, uses local JWTs bound to local sessions, and has no tenant dimension. The V1 UI is a framework-neutral local shell; optional external UI integrations do not change the core governance model. The CLI supports human-readable and structured output but does not turn scripting mode into an approval bypass.

## Security boundaries

The local encrypted vault, SecretManager, PKI, log redaction, audit trail, authentication, RBAC, and session manager are cross-cutting controls. Configuration artifacts may contain `secret://` references, but they do not resolve secrets into exports or logs. Deployment drivers receive only the declared references and controlled artifact data after the deployment layer has passed its policy gates.

The Docker baseline runs as a non-root user, stores state in a dedicated persistent volume, binds the compose port to localhost by default, drops Linux capabilities, uses `no-new-privileges`, and keeps the container filesystem read-only except for the state volume and temporary filesystem. These controls are a baseline and must be reviewed against the target environment.

## Evidence and claim discipline

The following are intentionally not claims made by V1:

- full autonomous operation;
- protocol emulation or full-fidelity digital-twin behavior without matching evidence;
- automatic production deployment without approvals, backups, verification, and rollback readiness;
- compliance certification or regulatory readiness;
- equivalence to a human engineer;
- correctness of an unsupported vendor, model, command, public prefix, ASN, floor dimension, or site fact;
- clinical, legal, or safety certification.

Benchmarking may report measured rates and confidence intervals, bounded by corpus, sample size, evidence IDs, and limitations. It may not convert those measurements into a broader maturity or equivalence claim.

## Extension rules

New components must preserve the following invariants: every non-trivial decision has a DecisionRecord or equivalent provenance; every non-inferable value remains human-supplied or explicitly assumed; every production-affecting path has governance and audit integration; every external result has an evidence status; every export is secret-safe; every state change has a SoT domain; and every adapter delegates business behavior to an orchestrator or service boundary.
