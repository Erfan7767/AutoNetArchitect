CREATE TABLE `project_site_business_requirements` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`site_reference` varchar(160) NOT NULL,
	`branch_role` varchar(120) NOT NULL,
	`service_priorities` varchar(2000) NOT NULL,
	`availability_objective` varchar(1000) NOT NULL,
	`jurisdiction_constraints` varchar(2000) NOT NULL,
	`human_mandatory_fields` varchar(4000) NOT NULL DEFAULT '[]',
	`review_state` enum('draft','reviewed') NOT NULL DEFAULT 'draft',
	`reviewed_at` timestamp,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `project_site_business_requirements_id` PRIMARY KEY(`id`)
);
