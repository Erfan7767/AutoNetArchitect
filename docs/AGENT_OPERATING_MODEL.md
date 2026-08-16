# AutoNetArchitect Operating Model for Authorized Network Automation

## Purpose and Accountability

AutoNetArchitect is a hosted control plane paired with a site agent operated inside an authorized management network. It is designed to automate repeatable engineering work while preserving evidence, uncertainty, and human accountability. It does not claim autonomous replacement of a professional network engineer, universal device compatibility, or production safety without measured and scoped proof.

The hosted control plane stores project intent, change plans, approvals, redacted artifacts, and audit records. The site agent performs only authorized device interactions using an outbound authenticated control connection. It does not receive raw secrets from the hosted application and it does not scan networks or configure devices outside a human-approved scope.

## Mandatory Pipeline

| Stage | Automatic action permitted | Evidence required | Execution effect |
|---|---|---|---|
| Scope registration | None | Named site, approved target range, allowed protocol, authority owner | No discovery without scope |
| Discovery | Read-only fact collection | Observed identity, platform, software release, interface inventory, and collector result | Unknown devices remain unresolved |
| Planning | Versioned artifact preparation | Requirements, device facts, capability evidence, rationale | No invented attributes or commands |
| Virtual validation | Submit a supported lab, digital-twin, or candidate-validation job | Artifact hash, target facts, test scope, adapter type, outcome, fidelity label | A pass permits review only |
| Release review | Evaluate controls | Current validation, backup, maintenance window, approval | Any missing control is no-go |
| Execution | Apply an already released plan | Target match, immutable approval, fresh backup | Stops on drift or integrity failure |
| Verification | Run the approved checks | Expected outcome and observed result | Failure starts scoped rollback evaluation |

## Virtual Validation Rule

Virtual validation is mandatory before a plan may request human release. Its states are `not_tested`, `test_queued`, `test_passed`, `test_failed`, `test_inconclusive`, and `not_supported_for_virtual_test`. Only a current `test_passed` result whose scope and artifact hash match the change plan can move a plan to human review.

> A virtual pass is not a production guarantee. It never replaces a capability check, a fresh backup, a valid maintenance window, a named human approval, or post-change verification.

The test adapter must identify whether it used a logical model, a virtualized vendor image, a physical lab, or a device-supported candidate/commit mechanism. The platform presents the evidence fidelity exactly as reported and blocks automatic execution for failed, stale, inconclusive, out-of-scope, or unsupported virtual tests.

## Supported Interface Principle

The site agent prefers documented interfaces exposed by the observed device. Cisco IOS XE documents NETCONF/YANG capability discovery and programmable configuration interfaces, alongside platform restrictions.[1] Juniper documents PyEZ as a client using NETCONF and Junos XML APIs.[2] Palo Alto Networks documents its PAN-OS XML API as an automation interface.[3]

No device is considered supported merely because its vendor name is known. A supported execution path requires observed platform and version facts, a matching adapter, an evidenced capability, and a validated configuration path.

## Security Rules

1. The control plane stores credential references and redacted metadata, never device passwords, private keys, tokens, or raw secrets.
2. Discovery is read-only until an approved change plan is released.
3. Production change execution is blocked without a named approver, fresh backup, valid maintenance window, and current target facts.
4. Logs, previews, and audit entries are redacted before they are available in the hosted interface.
5. Unsupported or ambiguous paths return an explicit block or safe refusal rather than a substituted command or estimate.

## References

[1] [Cisco IOS XE Programmability Configuration Guide — NETCONF Protocol](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/1713/b_1713_programmability_cg/m_1713_prog_yang_netconf.html)

[2] [Juniper — Set Up Junos PyEZ Managed Nodes](https://www.juniper.net/documentation/us/en/software/junos-pyez/junos-pyez-developer/topics/task/junos-pyez-client-configuring.html)

[3] [Palo Alto Networks — Getting Started with the PAN-OS XML API](https://docs.paloaltonetworks.com/pan-os/10-2/pan-os-panorama-api)
