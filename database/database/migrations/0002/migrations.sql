ALTER TABLE leveling_guild ADD COLUMN leveling_blacklisted_channel BIGINT[];
ALTER TABLE leveling_guild DROP COLUMN leveling_blacklisted_channels;
ALTER TABLE leveling_guild ALTER COLUMN leveling_blacklisted_channel SET NOT NULL;