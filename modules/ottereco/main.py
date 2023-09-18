from typing import Dict, List

from disnake.ext import commands
import apgorm
import os

from modules.ottereco.database.model import EconomyGuild, EconomyUser
from modules.ottereco.utils.shop import ShopDropDownView


class Economy:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    
    async def start_bot_tasks(self):
        def clear_lists():
            # Cool down list for economy commands
            self.bot.economy_cooldowns = {}
        # Clear lists every minute
        self.bot.scheduler.add_job(clear_lists, "interval", minutes=1)

    async def initalize_database(self) -> None:
        self.bot.log.info("Initalizing Database")
        self.bot.log.info("Finding/Creating Economy Guilds")
        # Goes through each guild
        for guild in self.bot.guilds:
            try:
                # Attempts to find the guild in the database
                guild_data = await EconomyGuild.fetch(guild_id=guild.id)
            except apgorm.exceptions.ModelNotFound:
                self.bot.log.info(
                    f"Creating a New Economy guild for server: {guild.name} ({guild.id})")
                # Creates a new guild in the database if it doesn't exist
                guild_data = await EconomyGuild(guild_id=guild.id).create()
            # Goes through each member in the guild
            for member in guild.members:
                if member is member.bot:
                    continue
                try:
                    # Attempts to find the member in the database
                    await EconomyUser.fetch(user_id=member.id, guild_id=guild.id)
                    self.bot.log.info(
                        f"Found {member.name} ({member.id}) in the database for {guild.name} ({guild.id})")
                except apgorm.exceptions.ModelNotFound:
                    # Makes a new member in the database if it doesn't exist
                    await EconomyUser(user_id=member.id, guild_id=guild.id, balance=guild_data.economy_starting_balance).create()
                    self.bot.log.info(
                        f"Created {member.name} ({member.id}) in the database for {guild.name} ({guild.id})")
        self.bot.log.info("Completed Database Setup")

    async def enable_plugin(self):
        await self.initalize_database()
        # Loads cogs
        for cog in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/cogs"):
            if cog.endswith(".py") and not cog.startswith("__"):
                self.bot.log.info(f"Loading from Otter Economy: {cog[:-3]}")
                try:
                    self.bot.load_extension(f"modules.ottereco.cogs.{cog[:-3]}")
                except () as e:
                    self.bot.log.error(f"ERROR LOADING {cog[:-3]} {e}")
                    self.bot.log.error("UNLOADING OTTER ECO")
                    self.disable_plugin()
                # add shop dropdown (presistent)
                self.bot.add_view(ShopDropDownView(options=None))
        self.bot.loaded_plugins.append("ottereco")

    # Unloads plugin
    def disable_plugin(self):
        for cog in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/cogs"):
            if cog.endswith(".py"):
                self.bot.log.info(f"Loading from Otter Eco: {cog[:-3]}")
                try:
                    self.bot.unload_extention(f"modules.ottereco.cogs.{cog[:-3]}")
                except:
                    self.bot.log.error(f"ERROR UNLOADING {cog[:-3]}")
