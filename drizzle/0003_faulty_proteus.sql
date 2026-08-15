CREATE TABLE `project_bom_items` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`category` enum('device','optic','license','support','labor','rack','cable','spare') NOT NULL,
	`description` varchar(500) NOT NULL,
	`quantity` int NOT NULL,
	`cost_estimate` varchar(120) NOT NULL DEFAULT '',
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `project_bom_items_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `project_config_artifacts` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`vendor` varchar(120) NOT NULL,
	`device_name` varchar(160) NOT NULL,
	`artifact_summary` varchar(2000) NOT NULL DEFAULT '',
	`feature_guard` enum('pass','blocked','unknown') NOT NULL DEFAULT 'unknown',
	`unsupported_feature_log` varchar(2000) NOT NULL DEFAULT '',
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `project_config_artifacts_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `project_design_details` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`topology_summary` varchar(2000) NOT NULL DEFAULT '',
	`vlan_plan` varchar(2000) NOT NULL DEFAULT '',
	`ip_addressing_summary` varchar(2000) NOT NULL DEFAULT '',
	`decision_records` varchar(8000) NOT NULL DEFAULT '',
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `project_design_details_id` PRIMARY KEY(`id`),
	CONSTRAINT `project_design_details_project_id_unique` UNIQUE(`project_id`)
);
