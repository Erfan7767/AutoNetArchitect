CREATE TABLE `authorized_discovery_scopes` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`site_id` int NOT NULL,
	`scope_reference` varchar(200) NOT NULL,
	`target_allowlist` varchar(4000) NOT NULL,
	`cidr_allowlist` varchar(4000) NOT NULL,
	`protocol_allowlist` varchar(500) NOT NULL,
	`scope_hash` varchar(160) NOT NULL,
	`status` enum('active','revoked') NOT NULL DEFAULT 'active',
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `authorized_discovery_scopes_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
ALTER TABLE `discovery_runs` ADD `discovery_scope_id` int DEFAULT 0 NOT NULL;