# Virtual Validation Path Boundaries

AutoNetArchitect exposes three distinct validation-path contracts. These contracts produce immutable, hash-bound plans and never authorize production execution.

| Path | Fidelity label | Evidence meaning | Production authority |
|---|---|---|---|
| `lab` | `vendor_image_lab` | Evidence from an approved vendor-image or physical laboratory path; the exact lab result remains an external recorded artifact. | Never granted by the adapter. |
| `digital_twin` | `logical_intent_only` | Logical comparison of intended state and modeled behavior. It is not protocol emulation and does not establish physical-device fidelity. | Never granted by the adapter. |
| `vendor_candidate_commit` | `candidate_commit_evidence` | Evidence that a vendor-supported candidate/commit path was exercised within an exact artifact, target-facts, and scope binding. | Never granted by the adapter. |

Every plan requires an artifact hash, target-facts hash, and scope hash. A plan also records the vendor family, path class, fidelity label, evidence requirements, and an explicit limitation. A successful validation result remains subject to current device capability evidence, backup verification, maintenance-window controls, governance approval, and production change policy.

These adapters are contracts for validation planning. They do not open device sessions, push configuration, emulate protocols, or replace production change control. `test_passed` evidence from any path is therefore necessary but not sufficient for a production release.
