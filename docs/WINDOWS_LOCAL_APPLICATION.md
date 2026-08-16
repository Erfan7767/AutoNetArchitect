# Windows Local Application Boundary

## Intended operating model

The Windows application is designed for an engineer working from a laptop inside an authorized customer management network. It keeps its project workspace locally, records only secret references, and requires an explicit approved discovery scope before contacting any address.

| Stage | Local application behavior | Boundary |
|---|---|---|
| Scope approval | Stores site identifier, approved CIDRs, explicit target allowlist, protocol allowlist, user acknowledgement, and approval reference | Does not store passwords, private keys, or tokens. |
| Discovery | Reviews the local Windows ARP cache and runs read-only, bounded evidence collection against explicitly approved targets | Does not infer vendor, platform, version, topology, or capability from ARP or an open TCP port. |
| Design | Builds evidence-backed artifacts from supplied requirements and observed facts | Abstains when mandatory requirements or evidence are missing. |
| Virtual validation | Binds an artifact hash, target-facts hash, and scope hash to a recorded result | A passed test is not production approval. |
| Execution | Reserved for separately approved supported paths | Requires backup, valid maintenance window, named approval, and post-change verification. |

## First release limitation

The initial Windows source shell implements approved-scope persistence, explicit target allowlists, consent acknowledgement, and a read-only reachability probe. It is not an installer and it does not yet contain vendor-specific authenticated collectors or configuration execution. A Windows device folder must be connected before a native installer can be built and tested. Until the application is code-signed through a user-controlled signing certificate and tested on a Windows endpoint, any manually packaged executable must be treated as an unsigned development artifact and reviewed by the operator before installation.

## Customer onboarding prerequisites

The engineer must provide the approved management scope, first device family/model/version, credential references managed outside the application, maintenance policy, and authorization boundary. The system must not generate those inputs or replace them with defaults.
