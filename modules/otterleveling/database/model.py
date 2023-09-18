import io
from enum import Enum
from typing import Optional

import apgorm
import apgorm as orm
import disnake
from apgorm.types import Array, BigInt, Boolean, Date, Int, Real, Serial, Text


class LevelingGuild(orm.Model):
    guild_id = BigInt().field()
    
    # LEVELING
    leveling_enabled = Boolean().field(default=False)
    # Leveling XP Per Message (min/max)
    leveling_xp_per_message_min = Int().field(default=0)
    leveling_xp_per_message_max = Int().field(default=0)
    # Level Up Messages
    leveling_xp_per_message_levelup_msg = Text().nullablefield(default=None)
    leveling_xp_per_message_levelup_channel = BigInt().nullablefield(default=None)
    # Multipliers
    leveling_server_multiplier = Real().field(default=1.0)
    # XP Base
    leveling_xp_base = Real().field(default=0.177)
    # Earnable Message per message before cooldown hits
    leveling_earnable_messages_per_min = Int().field(default=1)
    # Blacklisted Channels
    leveling_blacklisted_channel = Array(BigInt()).field(default=[])
    
    primary_key = (guild_id,)

class LevelRoles(orm.Model):
    # Ways to get the role data
    id = Serial().field()
    guild_id = BigInt().field()
    
    level = Int().field()
    # Role ID of the role
    role_id = BigInt().field()
    primary_key = (guild_id, id, )

    @staticmethod
    # Gets all the roles for a guild
    async def get_all_by_gid(guild_id: int):
        query = LevelRoles.fetch_query().where(LevelRoles.guild_id.eq(guild_id))
        return await query.fetchmany()
    
    
class LevelRoleMultplier(orm.Model):
    # Ways to get the multiplier data
    guild_id = BigInt().field()
    role_id = BigInt().field()
    # Multiplier
    multiplier = Real().field(default=1.0)

    primary_key = (role_id, )

    @staticmethod
    # Gets all the multipliers for a guild
    async def get_all_by_gid(guild_id: int):
        query = LevelRoleMultplier.fetch_query().where(LevelRoleMultplier.guild_id.eq(guild_id))
        return await query.fetchmany()
    
class LevelUsers(orm.Model):
    # Ways to get the user data
    guild_id = BigInt().field()
    user_id = BigInt().field()
    # XP
    xp = Int().field(default=0)

    primary_key = (guild_id, user_id)

    @staticmethod
    # Gets all the users for a guild
    async def get_everyone(guild_id: int):
        query = LevelUsers.fetch_query().where(LevelUsers.guild_id.eq(guild_id))
        return await query.fetchmany()