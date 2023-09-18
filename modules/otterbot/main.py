from typing import Dict, List

from disnake.ext import commands
import apgorm
import os



class OtterBot:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def enable_plugin(self):
        for cog in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/cogs"):
            if cog.endswith(".py") and not cog.startswith("__"):
                self.bot.log.info(f"Loading from Base Module: {cog[:-3]}")
                try:
                    self.bot.load_extension(f"modules.otterbot.cogs.{cog[:-3]}")
                except () as e:
                    self.bot.log.error(f"ERROR LOADING {cog[:-3]} {e}")
                    self.bot.log.error("UNLOADING BASE MODULE")
                    self.disable_plugin()
        self.bot.loaded_plugins.append("otterbot")

    def disable_plugin(self):
        for cog in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/cogs"):
            if cog.endswith(".py"):
                self.bot.log.info(f"Loading from Otter Verify: {cog[:-3]}")
                try:
                    self.bot.unload_extention(f"modules.otterbot.cogs.{cog[:-3]}")
                except:
                    self.bot.log.error(f"ERROR UNLOADING {cog[:-3]}")
