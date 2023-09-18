from enum import Enum
import io
from typing import Optional
import apgorm

import apgorm as orm
import disnake
from apgorm.types import BigInt, Boolean, Date, Text, Int, Serial, Real


class EconomyGuild(orm.Model):
    # Ways to indenitify the guild
    guild_id = BigInt().field()
    
    # ECONOMY
    economy_enabled = Boolean().field(default=False)
    economy_currency = Text().field(default="$")
    economy_currency_on_left = Boolean().field(default=True)
    # Starting balance for nwe users
    economy_starting_balance = Int().field(default=0)
    # Max balance
    economy_maximum_balance = Int().nullablefield(default=None)
    # $ per message
    economy_message_earnings_min = Int().field(default=1)
    economy_message_earnings_max = Int().field(default=0)
    # $ per /daily (per day)
    economy_daily_amount_min = Int().field(default=0)
    economy_daily_amount_max = Int().field(default=0)
    # $ per /work (per day)
    economy_work_amount_min = Int().field(default=0)
    economy_work_amount_max = Int().field(default=0)
    # Server-wide multi[lier
    economy_server_multiplier = Real().field(default=1.0)
    # Earnable messages for minute before cooldown kicks in
    economy_earnable_messages_per_min = Int().field(default=1)
    economy_log_channel = BigInt().nullablefield(default=None)
    
    primary_key = (guild_id,)
    
    
class PurchasableRole(orm.Model):
    # ways to identify the role
    id = Serial().field()
    guild_id = BigInt().field()
    role_id = BigInt().field()
    # Price of the role
    price = Int().field(default=0)

    primary_key = (id,)

    @staticmethod
    # Gets all purchasable roles by guild id
    async def get_all_by_gid(guild_id: int) -> apgorm.LazyList:
        query = PurchasableRole.fetch_query().where(PurchasableRole.guild_id.eq(guild_id))
        return await query.fetchmany()
    
class EconomyRoleIncome(orm.Model):
    # Gets ways to indentify the role
    id = Serial().field()
    guild_id = BigInt().nullablefield(default=None)
    role_id = BigInt().nullablefield(default=None)
    # Get min/max income per day
    min_income = Int().field(default=0)
    max_income = Int().field(default=0)

    primary_key = (id,)

    @staticmethod
    # Gets all guild roles by guild id
    async def get_all_by_gid(guild_id: int):
        query = EconomyRoleIncome.fetch_query().where(EconomyRoleIncome.guild_id.eq(guild_id))
        return await query.fetchmany()

class EconomyRoleMultplier(orm.Model):
    # Get ways to identify the role
    id = Serial().field()
    guild_id = BigInt().nullablefield(default=None)
    role_id = BigInt().nullablefield(default=None)
    # Multiplier for the role
    multiplier = Real().field(default=0)

    primary_key = (id,)

    @staticmethod
    async def get_all_by_gid(guild_id: int) -> apgorm.LazyList:
        # Gets all roles by guild id
        query = EconomyRoleMultplier.fetch_query().where(EconomyRoleMultplier.guild_id.eq(guild_id))
        return await query.fetchmany()
    
class EconomyUser(orm.Model):
    # ways to identify the user
    guild_id = BigInt().field()
    user_id = BigInt().field()
    # user balance
    balance = Int().field(default=0)
    # Last dates for cooldowns
    last_daily = Date().nullablefield(default=None)
    last_message = Date().nullablefield(default=None)
    last_work = Date().nullablefield(default=None)
    last_role_income = Date().nullablefield(default=None)
    # Multiplier for the user
    multiplier = Real().field(default=1.0)
    primary_key = (guild_id, user_id)
    
    
    @staticmethod
    # Gets all users by guild id
    async def get_everyone(guild_id: int):
        query = EconomyUser.fetch_query().where(EconomyUser.guild_id.eq(guild_id))
        return await query.fetchmany()
