CREATE TABLE `project_engineering_review_reports` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`report_reference` varchar(200) NOT NULL,
	`findings_json` varchar(8000) NOT NULL,
	`passed_count` int NOT NULL,
	`failed_count` int NOT NULL,
	`blocked_count` int NOT NULL,
	`unresolved_count` int NOT NULL,
	`assumptions` varchar(4000) NOT NULL DEFAULT '',
	`risks` varchar(4000) NOT NULL DEFAULT '',
	`evidence_gaps` varchar(4000) NOT NULL DEFAULT '',
	`required_human_actions` varchar(4000) NOT NULL DEFAULT '',
	`recorded_by` varchar(160) NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `project_engineering_review_reports_id` PRIMARY KEY(`id`)
);
