# Template CLI evidence findings

## Cisco IOS XE

The official Cisco IOS XE 17 command-reference landing page is https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/products-command-reference-list.html. The page exposes command-reference groups by IOS XE release, including 17.15.x, 17.14.x, 17.13.x, 17.12.x and earlier releases, and separates platform-specific references such as Catalyst 9200/9300/9400/9500/9600. Registry entries should therefore remain version- and model-scoped rather than making a universal IOS XE syntax claim.

## FortiOS

The official FortiOS 8.0.0 CLI reference is https://docs.fortinet.com/document/fortigate/8.0.0/cli-reference/84566/fortios-cli-reference. The page states that the reference describes FortiOS 8.0.0 CLI commands and warns that command availability varies by FortiGate model and hardware configuration. FortiGate template metadata must therefore carry a version and model/capability scope and cannot be treated as universally valid across FortiGate devices.

## Governance implication

The template registry uses evidence references and explicit validation-state metadata. Templates without a model/version-specific authoritative evidence chain remain validation-blocked or preview-only; the renderer does not upgrade them into production-safe claims.

## PAN-OS

The official Palo Alto Networks CLI hierarchy page is https://docs.paloaltonetworks.com/ngfw/pan-os-cli-quick-start/cli-command-hierarchy. It identifies configure CLI command hierarchies by PAN-OS releases including 11.1, 11.2, 12.1, and 12.2. PAN-OS templates must therefore remain release-scoped and should not claim universal syntax across all PAN-OS versions.

## Junos

The official Junos CLI Reference is https://www.juniper.net/documentation/us/en/software/junos/cli-reference/index.html. It covers CLI commands, configuration statements, and operational commands. Junos templates should keep command/configuration statement evidence distinct from generic configuration formatting and remain subject to version/model validation.
