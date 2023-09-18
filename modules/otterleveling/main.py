from typing import Dict, List

from disnake.ext import commands
import apgorm
import os

from modules.otterleveling.database.model import LevelingGuild, LevelUsers


class Leveling:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Setups Clearing Systems for cooldowns
    async def start_bot_tasks(self):
        def clear_lists():
            # XP Cooldown
            self.bot.xp_cooldown = {}
            # Holds user ID as they get XP (to prevent multiple level ups and xp spam)
            self.bot.xp_temp = []
        # Runs the function every minute
        self.bot.scheduler.add_job(clear_lists, "interval", minutes=1)

    # Initalizes the data for the leveling system
    async def initalize_database(self) -> None:
        self.bot.log.info("Initalizing Database")
        self.bot.log.info("Finding/Creating Leveling Guilds")
        # Goes through each guild
        for guild in self.bot.guilds:
            try:
                # Attempts to gets the Guild Data
                await LevelingGuild.fetch(guild_id=guild.id)
            except apgorm.exceptions.ModelNotFound:
                # If exception, create the guild data
                self.bot.log.info(
                    f"Creating a New Leveling guild for server: {guild.name} ({guild.id})")
                await LevelingGuild(guild_id=guild.id).create()
            finally:
                # Create each member in the database for that guild once guild data is created
                for member in guild.members:
                    # Filter Bots
                    if member is member.bot:
                        continue
                    try:
                        # Attempts to get level user data
                        await LevelUsers.fetch(user_id=member.id, guild_id=guild.id)
                        self.bot.log.info(
                            f"Found {member.name} ({member.id}) in the database for {guild.name} ({guild.id})")
                    except apgorm.exceptions.ModelNotFound:
                        # Create level user data
                        await LevelUsers(user_id=member.id, guild_id=guild.id).create()
                        self.bot.log.info(
                            f"Created {member.name} ({member.id}) in the database for {guild.name} ({guild.id})")
        self.bot.log.info("Completed Database Setup")

    # Loads the plugin
    async def enable_plugin(self):
        # Runs the initailize database function
        await self.initalize_database()
        # Goes through each cog and loads it
        for cog in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/cogs"):
            if cog.endswith(".py") and not cog.startswith("__"):
                self.bot.log.info(f"Loading from Otter Leveling: {cog[:-3]}")
                try:
                    self.bot.load_extension(f"modules.otterleveling.cogs.{cog[:-3]}")
                except () as e:
                    self.bot.log.error(f"ERROR LOADING {cog[:-3]} {e}")
                    self.bot.log.error("UNLOADING OTTER Leveling")
                    self.disable_plugin()
        self.bot.loaded_plugins.append("otterleveling")

    # Unloads the plugin
    def disable_plugin(self):
        for cog in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/cogs"):
            if cog.endswith(".py"):
                self.bot.log.info(f"Loading from Otter Leveling: {cog[:-3]}")
                try:
                    self.bot.unload_extention(f"modules.otterleveling.cogs.{cog[:-3]}")
                except:
                    self.bot.log.error(f"ERROR UNLOADING {cog[:-3]}")
