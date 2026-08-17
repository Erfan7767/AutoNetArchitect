CREATE TABLE `device_rollback_eligibility_assessments` (
	`id` int AUTO_INCREMENT NOT NULL,
	`device_id` int NOT NULL,
	`rollback_artifact_hash` varchar(160) NOT NULL,
	`configuration_path_reference` varchar(1000) NOT NULL,
	`target_facts_hash` varchar(160) NOT NULL,
	`scope_hash` varchar(160) NOT NULL,
	`decision` enum('eligible','review_required','ineligible') NOT NULL,
	`evidence_reference` varchar(1000) NOT NULL,
	`human_reviewer` varchar(160) NOT NULL,
	`assessed_at` timestamp NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `device_rollback_eligibility_assessments_id` PRIMARY KEY(`id`)
);
