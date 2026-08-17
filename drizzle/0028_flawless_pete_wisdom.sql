CREATE TABLE `inventory_interface_evidence` (
	`id` int AUTO_INCREMENT NOT NULL,
	`site_id` int NOT NULL,
	`device_id` int NOT NULL,
	`discovery_run_id` int NOT NULL,
	`discovery_scope_id` int NOT NULL,
	`interface_reference` varchar(300) NOT NULL,
	`state` enum('observed','inferred','unknown') NOT NULL,
	`evidence_reference` varchar(1000) NOT NULL,
	`evidence_hash` varchar(160) NOT NULL,
	`inference_rationale` varchar(2000) NOT NULL DEFAULT '',
	`observed_at` timestamp NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `inventory_interface_evidence_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `inventory_link_evidence` (
	`id` int AUTO_INCREMENT NOT NULL,
	`site_id` int NOT NULL,
	`discovery_run_id` int NOT NULL,
	`discovery_scope_id` int NOT NULL,
	`endpoint_a_device_id` int NOT NULL,
	`endpoint_a_interface_reference` varchar(300) NOT NULL,
	`endpoint_b_device_id` int NOT NULL DEFAULT 0,
	`endpoint_b_interface_reference` varchar(300) NOT NULL,
	`topology_state` enum('observed','inferred','unknown') NOT NULL,
	`evidence_reference` varchar(1000) NOT NULL,
	`evidence_hash` varchar(160) NOT NULL,
	`inference_rationale` varchar(2000) NOT NULL DEFAULT '',
	`observed_at` timestamp NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `inventory_link_evidence_id` PRIMARY KEY(`id`)
);
