# Vendor Support Sources

AutoNetArchitect's initial vendor scope is limited to Cisco, Huawei, Fortinet, and HPE Aruba. These references constrain interface decisions; they do not establish compatibility for every model, release, license, or feature.

## Cisco IOS XE

Cisco documents NETCONF over SSH, YANG models, capability discovery, and model-based operations for IOS XE.

Source: https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/1713/b_1713_programmability_cg/m_1713_prog_yang_netconf.html

## Huawei VRP / CloudEngine

Huawei documents RESTCONF and NETCONF as distinct management paths. Exact product family and software release must be observed before a workflow is selected.

Source: https://support.huawei.com/enterprise/en/doc/EDOC1100278266/d73bfdce/overview-of-restconf

## Fortinet FortiGate / FortiOS

Fortinet documents token-based API access, least-privilege API administrators, and trusted hosts. Tokens remain local secret-manager references and never enter source, artifacts, logs, or audit details.

Source: https://docs.fortinet.com/document/fortigate/8.0.0/administration-guide/940602/using-apis

## HPE Aruba AOS-CX

HPE Aruba documents AOS-CX REST API access, read-only versus read-write modes, HTTPS VRF enablement, session handling, and CSRF requirements for supported releases.

Source: https://developer.arubanetworks.com/aoscx/docs/introduction

## Policy

Observed vendor family, platform, software version, license, management interface, and required feature evidence are mandatory. Vendor name alone is insufficient. Unknown or ambiguous devices are unsupported or require review. The system must not synthesize commands, declare production readiness, claim compliance certification, or claim engineer equivalence from these references.

This document is documentation-only evidence. It never authorizes a device change.

Last reviewed: 2026-08-16
