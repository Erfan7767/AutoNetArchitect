ALTER TABLE `managed_devices` ADD `discovery_run_id` int DEFAULT 0 NOT NULL;--> statement-breakpoint
ALTER TABLE `managed_devices` ADD `discovery_scope_id` int DEFAULT 0 NOT NULL;