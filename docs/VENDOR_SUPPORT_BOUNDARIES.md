# Vendor Support Boundaries

## Scope

AutoNetArchitect currently exposes a **read-only discovery contract** for four vendor families relevant to the initial Saudi-market support boundary: Cisco, Huawei, Fortinet, and HPE Aruba. The contract describes approved management protocols and the evidence required before any configuration path can be considered.

This document does not claim universal model coverage, version compatibility, protocol emulation, production safety, or certification readiness. A vendor-family match is not sufficient to generate or upload configuration.

| Vendor family | Read-only discovery protocols | Configuration state | Version policy | Required before configuration |
|---|---|---|---|---|
| Cisco | SSH, NETCONF, HTTPS API | Verification required | Not loaded | Exact platform, exact software version, license/entitlement, and configuration-path evidence |
| Huawei | SSH, NETCONF, HTTPS API | Verification required | Not loaded | Exact platform, exact software version, license/entitlement, and configuration-path evidence |
| Fortinet FortiOS | SSH, HTTPS API | Verification required | Not loaded | Exact platform, exact software version, license/entitlement, and configuration-path evidence |
| HPE Aruba AOS-CX | SSH, HTTPS API | Verification required | Not loaded | Exact platform, exact software version, license/entitlement, and configuration-path evidence |

## Evidence rules

The registry rejects an unknown vendor as unsupported. It marks a known vendor with an unrecognized platform as requiring review. It rejects a protocol outside the vendor contract. It requires a non-empty software version and device identity reference. It requires an explicit version policy before configuration support can be granted; a non-empty version string alone is not evidence of compatibility. It also requires license evidence, requested capability evidence, and a verified configuration path.

The default policy data intentionally contains empty `supported_version_prefixes` and a `verification_required` status for every vendor family. The policy also records candidate release-note leads without treating them as compatibility approvals: Cisco Catalyst IOS XE 17.18 and 17.17, FortiOS 8.0, and AOS-CX 10.14 are recorded with official source links; Huawei has no candidate release loaded until a platform-specific official release record is reviewed. This is a safe boundary: an administrator must load a reviewed, traceable policy for an exact platform/version path before configuration support can move beyond review.

## Discovery adapters

The vendor adapters create **evidence request plans only**. They do not synthesize CLI commands, substitute generic commands, open sessions, alter devices, or expose credential values. Credential references remain opaque identifiers. Fortinet plans include an explicit virtual-domain summary evidence request because multi-VDOM context must not be silently inferred.

## Virtual validation boundary

The initial virtual adapter contracts are labelled `logical_intent_only`. They bind the artifact hash, target-facts hash, and authorized scope hash, and they produce a queued validation plan. Logical validation is not protocol emulation and cannot authorize a production change. Production release remains subject to the existing virtual-test, backup, human approval, maintenance-window, and device-capability gates.

## Authoritative references

The registry stores official documentation URLs as evidence-source references. These links identify protocol or API documentation; they do not by themselves prove compatibility for a particular model, release, license, or customer environment.

1. Cisco programmability and NETCONF documentation: [Cisco IOS XE Programmability Configuration Guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/1713/b_1713_programmability_cg/m_1713_prog_yang_netconf.html).
2. Huawei RESTCONF documentation: [Huawei Enterprise RESTCONF overview](https://support.huawei.com/enterprise/en/doc/EDOC1100278266/d73bfdce/overview-of-restconf).
3. Fortinet API documentation: [FortiGate Administration Guide — Using APIs](https://docs.fortinet.com/document/fortigate/8.0.0/administration-guide/940602/using-apis).
4. HPE Aruba AOS-CX API documentation: [AOS-CX API introduction](https://developer.arubanetworks.com/aoscx/docs/introduction).
