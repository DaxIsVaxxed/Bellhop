
from disnake.ext import commands
import apgorm
import os

from modules.ottermail.cogs.modmail import ModmailButton
from modules.ottermail.database.model import ModmailGuild


class Modmail:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Initialize the database and create a ModmailGuild for each guild the bot is in
    async def initalize_database(self):
        self.bot.log.info("Initalizing Database")
        self.bot.log.info("Finding/Creating Modmail Guilds")
        # Guild Databases for Modmail Configuration
        for guild in self.bot.guilds:
            try:
                await ModmailGuild.fetch(guild_id=guild.id)
            except apgorm.exceptions.ModelNotFound:
                self.bot.log.info(f"Creating a New Modmail guild for server: {guild.name} ({guild.id})")
                await ModmailGuild(guild_id=guild.id).create()
            self.bot.log.info("Completed Database Setup")

    # Enables the plugin
    async def enable_plugin(self):
        await self.initalize_database()
        # Loads all the modmail cogs
        for cog in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/cogs"):
            if cog.endswith(".py") and not cog.startswith("__"):
                self.bot.log.info(f"Loading from Otter Mail: {cog[:-3]}")
                try:
                    self.bot.load_extension(f"modules.ottermail.cogs.{cog[:-3]}")
                except () as e:
                    self.bot.log.error(f"ERROR LOADING {cog[:-3]} {e}")
                    self.bot.log.error("UNLOADING OTTERMAIL")
                    self.disable_plugin()
        try:
            # Presists the Modmail Button
            self.bot.add_view(ModmailButton())
        except () as e:
            self.bot.log.error(f"ERROR LOADING {cog[:-3]} {e})")
            self.bot.log.error("UNLOADING OTTERMAIL")
            self.disable_plugin()
        self.bot.loaded_plugins.append("ottermail")

    def disable_plugin(self):
        for cog in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/cogs"):
            if cog.endswith(".py"):
                self.bot.log.info(f"Loading from OtterMAIL: {cog[:-3]}")
                try:
                    self.bot.unload_extention(f"modules.ottermail.cogs.{cog[:-3]}")
                except:
                    self.bot.log.error(f"ERROR UNLOADING {cog[:-3]}")
