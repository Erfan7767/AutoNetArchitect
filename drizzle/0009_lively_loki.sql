CREATE TABLE `discovery_runs` (
	`id` int AUTO_INCREMENT NOT NULL,
	`site_id` int NOT NULL,
	`mode` enum('read_only') NOT NULL DEFAULT 'read_only',
	`state` enum('queued','running','completed','partial','failed','blocked') NOT NULL DEFAULT 'queued',
	`scope_hash` varchar(160) NOT NULL,
	`evidence_summary` varchar(4000) NOT NULL DEFAULT '',
	`evidence_hash` varchar(160) NOT NULL DEFAULT '',
	`ambiguous_count` int NOT NULL DEFAULT 0,
	`unsupported_count` int NOT NULL DEFAULT 0,
	`started_at` timestamp,
	`completed_at` timestamp,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `discovery_runs_id` PRIMARY KEY(`id`)
);
