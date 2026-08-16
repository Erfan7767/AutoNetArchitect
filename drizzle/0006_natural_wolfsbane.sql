CREATE TABLE `change_plans` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`name` varchar(200) NOT NULL,
	`artifact_hash` varchar(160) NOT NULL,
	`target_facts_hash` varchar(160) NOT NULL,
	`scope_hash` varchar(160) NOT NULL,
	`virtual_validation_state` enum('not_tested','test_queued','test_passed','test_failed','test_inconclusive','not_supported_for_virtual_test') NOT NULL DEFAULT 'not_tested',
	`release_state` enum('draft','blocked','ready_for_approval','approved','executed','rolled_back') NOT NULL DEFAULT 'draft',
	`backup_verified` boolean NOT NULL DEFAULT false,
	`maintenance_window_valid` boolean NOT NULL DEFAULT false,
	`human_approver` varchar(160),
	`approved_at` timestamp,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `change_plans_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `managed_devices` (
	`id` int AUTO_INCREMENT NOT NULL,
	`site_id` int NOT NULL,
	`device_reference` varchar(200) NOT NULL,
	`management_address` varchar(255) NOT NULL,
	`protocol` enum('ssh','netconf','https_api','snmp') NOT NULL,
	`credential_reference` varchar(160) NOT NULL,
	`observed_vendor` varchar(120) NOT NULL DEFAULT '',
	`observed_platform` varchar(160) NOT NULL DEFAULT '',
	`observed_version` varchar(160) NOT NULL DEFAULT '',
	`fact_state` enum('unobserved','observed','ambiguous','unreachable','unsupported') NOT NULL DEFAULT 'unobserved',
	`facts_hash` varchar(160) NOT NULL DEFAULT '',
	`last_observed_at` timestamp,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `managed_devices_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `managed_sites` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`name` varchar(160) NOT NULL,
	`agent_reference` varchar(160) NOT NULL DEFAULT '',
	`approved_scope_reference` varchar(200) NOT NULL,
	`mode` enum('read_only','prepared_change') NOT NULL DEFAULT 'read_only',
	`enrollment_state` enum('not_enrolled','pending','active','revoked') NOT NULL DEFAULT 'not_enrolled',
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `managed_sites_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `virtual_test_runs` (
	`id` int AUTO_INCREMENT NOT NULL,
	`change_plan_id` int NOT NULL,
	`state` enum('not_tested','test_queued','test_passed','test_failed','test_inconclusive','not_supported_for_virtual_test') NOT NULL,
	`adapter_kind` varchar(120) NOT NULL,
	`fidelity_label` varchar(120) NOT NULL,
	`artifact_hash` varchar(160) NOT NULL,
	`target_facts_hash` varchar(160) NOT NULL,
	`scope_hash` varchar(160) NOT NULL,
	`detail` varchar(1000) NOT NULL DEFAULT '',
	`observed_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `virtual_test_runs_id` PRIMARY KEY(`id`)
);
