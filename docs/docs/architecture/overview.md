# Architecture overview

AutoNetArchitect is organized as a layered control plane. Questionnaire and requirements capture human inputs. Knowledge and evidence governance preserve source, freshness, and claim scope. Designers and the decision engine generate alternatives, decisions, assumptions, and abstentions. Equipment and configuration layers consume capability evidence and retain artifact provenance. Governance, supervised mode, review control, and orchestrators regulate transitions. Persistence and Source of Truth managers preserve state. CLI, API, and UI are adapters over these boundaries.

The canonical workflow is questionnaire, requirements, design, equipment, configuration generation, deployment preparation, deployment execution, operations, compliance, and reports. A caller cannot skip a stage merely because an artifact exists. A blocked outcome does not silently mutate the workflow state.

The system distinguishes logical design feasibility, field feasibility, formal verification evidence, simulation evidence, discovered operational evidence, inferred transient state, and replayed historical state. Reports must state which basis supports a claim.

## Architecture invariants

| Invariant | Enforcement boundary |
|---|---|
| Human-mandatory values are not guessed | Requirements, field reality, designers, and gates |
| Secrets are references outside the secret boundary | SecretManager, redaction, exporters, reports, audit |
| Production-affecting actions are supervised | Governance, review control, deployment orchestrators |
| Unsupported capability is not approximated | Equipment matrix and config feature guards |
| State transitions are traceable | Persistence, SoT, audit, and orchestrators |
| CI checks are mandatory for repository changes | GitHub/GitLab gate jobs and branch protection |
