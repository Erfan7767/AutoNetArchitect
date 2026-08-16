ALTER TABLE `change_plans` ADD `sector_profile_snapshot` varchar(8000) DEFAULT '{}' NOT NULL;--> statement-breakpoint
ALTER TABLE `change_plans` ADD `sector_inputs_hash` varchar(160) DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `change_plans` ADD `sector_review_state` enum('current','stale','missing') DEFAULT 'missing' NOT NULL;--> statement-breakpoint
ALTER TABLE `change_plans` ADD `sector_reviewed_at` timestamp;--> statement-breakpoint
ALTER TABLE `network_projects` ADD `sector_inputs_updated_at` timestamp;