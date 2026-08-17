CREATE TABLE `project_lab_authorizations` (
	`id` int AUTO_INCREMENT NOT NULL,
	`project_id` int NOT NULL,
	`site_id` int NOT NULL,
	`scope_hash` varchar(160) NOT NULL,
	`authorization_reference` varchar(300) NOT NULL,
	`human_authorizer` varchar(160) NOT NULL,
	`environment_reference` varchar(300) NOT NULL,
	`environment_class` enum('isolated_simulation','vendor_image_lab','physical_lab') NOT NULL,
	`approved_at` timestamp NOT NULL,
	`expires_at` timestamp NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `project_lab_authorizations_id` PRIMARY KEY(`id`)
);
