CREATE TABLE `change_plan_backup_receipts` (
	`id` int AUTO_INCREMENT NOT NULL,
	`change_plan_id` int NOT NULL,
	`backup_reference` varchar(1000) NOT NULL,
	`backup_artifact_hash` varchar(160) NOT NULL,
	`target_facts_hash` varchar(160) NOT NULL,
	`scope_hash` varchar(160) NOT NULL,
	`verification_state` enum('captured','verified','rejected') NOT NULL DEFAULT 'captured',
	`human_verifier` varchar(160) NOT NULL,
	`verified_at` timestamp NOT NULL DEFAULT (now()),
	`automatic_capture_permitted` boolean NOT NULL DEFAULT false,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `change_plan_backup_receipts_id` PRIMARY KEY(`id`)
);
