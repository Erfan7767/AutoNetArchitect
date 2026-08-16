CREATE TABLE `device_capability_assessments` (
	`id` int AUTO_INCREMENT NOT NULL,
	`device_id` int NOT NULL,
	`observed_vendor` varchar(120) NOT NULL,
	`observed_platform` varchar(160) NOT NULL,
	`observed_model` varchar(160) NOT NULL,
	`observed_version` varchar(160) NOT NULL,
	`capability_evidence_reference` varchar(1000) NOT NULL,
	`license_evidence_reference` varchar(1000) NOT NULL,
	`configuration_path_evidence_reference` varchar(1000) NOT NULL,
	`decision` enum('configuration_supported','review_required','unsupported') NOT NULL,
	`assessed_at` timestamp NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `device_capability_assessments_id` PRIMARY KEY(`id`)
);
