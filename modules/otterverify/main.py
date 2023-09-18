from typing import Dict, List

from disnake.ext import commands
import apgorm
import os

from modules.otterverify.database.model import VerificationStatus, VerificationApp, VerificationGuild
from modules.otterverify.configurations.config import VerificationCategory, VerificationConfigData, VerificationConfiguration
from modules.otterverify.cogs.verification import QuestioningButtons, VerifyButton, ActionButton


class Verification:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Initalizling Databases with APGORM
    async def initalize_database(self):
        self.bot.log.info("Initalizing Database")
        self.bot.log.info("Finding/Creating Verification Guilds")
        # Create Verification Guild Data for each guild found.
        for guild in self.bot.guilds:
            try:
                await VerificationGuild.fetch(guild_id=guild.id)
            except apgorm.exceptions.ModelNotFound:
                self.bot.log.info(f"Creating a New Verification guild for server: {guild.name} ({guild.id})")
                await VerificationGuild(guild_id=guild.id).create()
            self.bot.log.info("Completed Database Setup")

    async def enable_plugin(self):
        await self.initalize_database()
        for cog in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/cogs"):
            if cog.endswith(".py") and not cog.startswith("__"):
                self.bot.log.info(f"Loading from Otter Verify: {cog[:-3]}")
                try:
                    self.bot.load_extension(f"modules.otterverify.cogs.{cog[:-3]}")
                except () as e:
                    self.bot.log.error(f"ERROR LOADING {cog[:-3]} {e}")
                    self.bot.log.error("UNLOADING OTTER VERIFY")
                    self.disable_plugin()
        try:
            self.bot.add_view(VerifyButton())
            self.bot.add_view(QuestioningButtons())
            self.bot.add_view(ActionButton())
        except () as e:
            self.bot.log.error(f"ERROR LOADING {cog[:-3]} {e})")
            self.bot.log.error("UNLOADING OTTER VERIFY")
            self.disable_plugin()
        self.bot.loaded_plugins.append("otterverify")

    def disable_plugin(self):
        for cog in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/cogs"):
            if cog.endswith(".py"):
                self.bot.log.info(f"Loading from Otter Verify: {cog[:-3]}")
                try:
                    self.bot.unload_extention(f"modules.otterverify.cogs.{cog[:-3]}")
                except:
                    self.bot.log.error(f"ERROR UNLOADING {cog[:-3]}")
