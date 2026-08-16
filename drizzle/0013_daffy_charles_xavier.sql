ALTER TABLE `managed_devices` ADD `capability_evidence_reference` varchar(1000) DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `managed_devices` ADD `license_evidence_reference` varchar(1000) DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `managed_devices` ADD `configuration_path_evidence_reference` varchar(1000) DEFAULT '' NOT NULL;