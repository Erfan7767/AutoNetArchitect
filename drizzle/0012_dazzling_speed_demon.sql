CREATE TABLE `benchmark_scenarios` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`scenario_id` varchar(200) NOT NULL,
	`vendor_family` enum('cisco','huawei','fortinet','hpe_aruba') NOT NULL,
	`platform` varchar(160) NOT NULL,
	`software_version` varchar(160) NOT NULL,
	`license_evidence_reference` varchar(1000) NOT NULL,
	`configuration_path_reference` varchar(1000) NOT NULL,
	`sector_profile` enum('enterprise','financial_service_branch','retail_transaction_branch','industrial') NOT NULL,
	`measured_runs` int NOT NULL,
	`accepted_runs` int NOT NULL,
	`rejected_runs` int NOT NULL,
	`evidence_reference` varchar(1000) NOT NULL,
	`reviewed_at` timestamp NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `benchmark_scenarios_id` PRIMARY KEY(`id`)
);
