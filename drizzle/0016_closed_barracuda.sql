CREATE TABLE `project_restricted_claims` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`claim_class` enum('engineer_equivalence','production_safe','compatibility','compliance') NOT NULL,
	`scope_description` varchar(1000) NOT NULL,
	`authority_reference` varchar(1000) NOT NULL,
	`measured_evidence_reference` varchar(1000) NOT NULL,
	`reviewed_at` timestamp,
	`assessment_status` enum('publishable','blocked') NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `project_restricted_claims_id` PRIMARY KEY(`id`)
);
