ALTER TABLE leveling_guild ADD COLUMN leveling_blacklisted_channels BIGINT[];
ALTER TABLE leveling_guild DROP COLUMN leveling_blacklisted_channel;
ALTER TABLE leveling_guild ALTER COLUMN leveling_blacklisted_channels SET NOT NULL;