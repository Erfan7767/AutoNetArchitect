CREATE TABLE `site_agent_enrollments` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`site_id` int NOT NULL,
	`agent_id` varchar(160) NOT NULL,
	`enrollment_id` varchar(160) NOT NULL,
	`agent_fingerprint` varchar(64) NOT NULL,
	`agent_public_key_pem` text NOT NULL,
	`scope_hash` varchar(160) NOT NULL,
	`status` enum('active','revoked','expired') NOT NULL DEFAULT 'active',
	`expires_at` timestamp NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `site_agent_enrollments_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `site_agent_health_reports` (
	`id` int AUTO_INCREMENT NOT NULL,
	`enrollment_id` int NOT NULL,
	`healthy` boolean NOT NULL,
	`mode` varchar(80) NOT NULL,
	`detail` varchar(500) NOT NULL,
	`observed_at` timestamp NOT NULL,
	`received_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `site_agent_health_reports_id` PRIMARY KEY(`id`)
);
