from disnake import Embed, GuildCommandInteraction, MessageInteraction
import disnake
from disnake.ext import commands
from modules.ottereco.database.model import EconomyGuild
from modules.ottereco.utils.embeds import otter_embed


# Formats currency based on params
def format_money(amount: int = 0, currency: str = "", currency_on_left: bool = True):
    if currency_on_left:
        return f"{currency}{amount}"
    else:
        return f"{amount} {currency}"

# Checks if economy is enabled for @economy_enabled()
def economy_enabled():
    async def predicate(ctx):
        guild = ctx.guild
        if guild is None:
            return False
        guild_data = await EconomyGuild.fetch(guild_id=guild.id)
        embed = otter_embed(ctx.author)
        if not guild_data.economy_enabled:
            embed.title = "Economy is disabled"
            embed.description = "Economy is disabled in this server. Please ask a server administrator to enable it."
            await ctx.send(embed=embed)
        return guild_data.economy_enabled

    return commands.check(predicate)

# Sends log to economy log channel
async def send_log(ctx: MessageInteraction | GuildCommandInteraction | disnake.Message | disnake.Member, embed: Embed, title: str, event: str):
    # If not in a guild disregard
    if ctx.guild is None:
        return
    # Get guild data
    guild_data = await EconomyGuild.fetch(guild_id=ctx.guild.id)
    # Modify embed
    embed.title = title
    embed.description = f"**Event:** {event}"
    # If logs are set, get it and send it there
    if guild_data.economy_log_channel is not None:
        channel = ctx.guild.get_channel(guild_data.economy_log_channel)
        if channel is not None and isinstance(channel, disnake.TextChannel):
            await channel.send(embed=embed)