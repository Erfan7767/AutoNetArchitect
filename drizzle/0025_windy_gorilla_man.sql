CREATE TABLE `change_plan_rollback_preparations` (
	`id` int AUTO_INCREMENT NOT NULL,
	`change_plan_id` int NOT NULL,
	`rollback_review_id` int NOT NULL,
	`rollback_artifact_hash` varchar(160) NOT NULL,
	`target_facts_hash` varchar(160) NOT NULL,
	`scope_hash` varchar(160) NOT NULL,
	`eligibility_state` enum('ready_for_human_execution','blocked') NOT NULL,
	`human_execution_required` boolean NOT NULL DEFAULT true,
	`automatic_execution_permitted` boolean NOT NULL DEFAULT false,
	`prepared_by` varchar(160) NOT NULL,
	`prepared_at` timestamp NOT NULL DEFAULT (now()),
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `change_plan_rollback_preparations_id` PRIMARY KEY(`id`)
);
