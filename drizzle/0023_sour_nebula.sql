CREATE TABLE `change_plan_rollback_reviews` (
	`id` int AUTO_INCREMENT NOT NULL,
	`change_plan_id` int NOT NULL,
	`rollback_scope_reference` varchar(1000) NOT NULL,
	`rollback_artifact_hash` varchar(160) NOT NULL,
	`target_facts_hash` varchar(160) NOT NULL,
	`scope_hash` varchar(160) NOT NULL,
	`backup_evidence_reference` varchar(1000) NOT NULL,
	`trigger` varchar(1000) NOT NULL,
	`review_state` enum('review_required','reviewed','blocked') NOT NULL DEFAULT 'review_required',
	`human_reviewer` varchar(160) NOT NULL,
	`reviewed_at` timestamp NOT NULL DEFAULT (now()),
	`automatic_execution_permitted` boolean NOT NULL DEFAULT false,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `change_plan_rollback_reviews_id` PRIMARY KEY(`id`)
);
