# Layers and boundaries

| Layer | Responsibility | What it must not claim |
|---|---|---|
| Requirements | Gather constraints, contradictions, mandatory inputs, assumptions, and requirements documents | It must not infer human-owned facts without evidence |
| Design and decision | Compare alternatives, record rationale, confidence, evidence, and no-decision outcomes | It must not convert confidence into proof |
| Equipment and configuration | Match vendor/model/license capabilities and render guarded artifacts | It must not substitute guessed commands |
| Formal verification and simulation | Check intents and logical behavior within supplied inputs | Simulation is not protocol emulation or production acceptance |
| Governance and supervised mode | Require reviewers, approvers, accountability, separation of duties, and audit | Authentication is not approval; a UI action is not execution authority |
| Deployment | Prepare or execute controlled changes with backup, verification, rollback, and no-go gates | It must not execute an unresolved or unapproved path |
| Operations | Collect read-only evidence, detect drift, support diagnosis and incident response | It must not auto-remediate high-risk production drift without approval |
| Compliance | Map technical controls to declared evidence and scope | It must not issue certification or regulatory readiness |
| CI/CD | Enforce repository quality, security, reproducibility, and release artifact checks | Passing CI does not approve a network change |

Every cross-layer result should preserve project ID, workflow ID, stage, actor, timestamp, SoT domain, evidence references, assumptions, confidence or proof status, and audit references. The exact record type depends on the layer but the provenance contract remains.
