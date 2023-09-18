import math

import disnake
from disnake import Embed, GuildCommandInteraction
from disnake.ext import commands

from modules.otterleveling.database.model import LevelingGuild
from modules.otterleveling.utils.embeds import otter_embed


# Converts XP to Level (Base is 0.177 by default)
def convertXPToLevel(xp, base=0.177):
    # For Reference: sqrt(xp) * base
    return int(math.floor(math.sqrt(xp) * base))


# Convert Level to XP (Base is 0.177 by default)
def convertLevelToXP(level, base=0.177):
    # For Reference: floor(level/base)^2
    return int(math.floor(((level) / base) ** 2))

# Checks if leveling is enabled in the guild (@leveling_enabled())
def leveling_enabled():
    async def predicate(ctx):
        guild = ctx.guild
        if guild is None:
            return False
        guild_data = await LevelingGuild.fetch(guild_id=guild.id)
        if guild_data is None:
            return False
        if not guild_data.leveling_enabled:
            embed = otter_embed(ctx.author)
            embed.title = "Leveling is not enabled"
            embed.description = "Leveling is not enabled in this server. Contact an server administrator to enable it."
            await ctx.send(embed=embed, ephemeral=True)
        return guild_data.leveling_enabled

    return commands.check(predicate)

