CREATE TABLE `post_change_verification_runs` (
	`id` int AUTO_INCREMENT NOT NULL,
	`change_plan_id` int NOT NULL,
	`state` enum('passed','failed','warning','not_verifiable') NOT NULL,
	`verification_type` enum('command_verification','connectivity_verification','service_verification','routing_verification','monitoring_verification','user_verification') NOT NULL,
	`expected_outcome` varchar(1000) NOT NULL,
	`observed_outcome` varchar(2000) NOT NULL,
	`evidence_reference` varchar(1000) NOT NULL,
	`rollback_review_required` boolean NOT NULL DEFAULT false,
	`recorded_by` varchar(160) NOT NULL,
	`observed_at` timestamp NOT NULL DEFAULT (now()),
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `post_change_verification_runs_id` PRIMARY KEY(`id`)
);
