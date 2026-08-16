ALTER TABLE `benchmark_scenarios` ADD `model` varchar(160) NOT NULL;--> statement-breakpoint
ALTER TABLE `managed_devices` ADD `observed_model` varchar(160) DEFAULT '' NOT NULL;