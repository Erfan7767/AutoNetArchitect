CREATE TABLE `audit_events` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`actor_id` int NOT NULL,
	`actor_name` varchar(160) NOT NULL,
	`action` varchar(100) NOT NULL,
	`details` text NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `audit_events_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `network_projects` (
	`id` int AUTO_INCREMENT NOT NULL,
	`owner_id` int NOT NULL,
	`name` varchar(160) NOT NULL,
	`organization` varchar(160) NOT NULL DEFAULT '',
	`organization_type` varchar(120) NOT NULL DEFAULT '',
	`site_count` int NOT NULL DEFAULT 0,
	`classification` enum('greenfield','brownfield','undetermined') NOT NULL DEFAULT 'undetermined',
	`vendor_preferences` varchar(1000) NOT NULL DEFAULT '',
	`compliance_needs` varchar(1000) NOT NULL DEFAULT '',
	`status` enum('intake','design','ready_for_review','approved') NOT NULL DEFAULT 'intake',
	`questionnaire_complete` int NOT NULL DEFAULT 0,
	`requirements_complete` int NOT NULL DEFAULT 0,
	`approval_state` enum('not_requested','pending','approved','blocked') NOT NULL DEFAULT 'not_requested',
	`approved_by` varchar(160),
	`approved_at` timestamp,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `network_projects_id` PRIMARY KEY(`id`)
);
