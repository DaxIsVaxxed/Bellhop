import importlib
from typing import List

from disnake.ext import commands
import disnake

from modules.otterbot.utils.config_menu import ConfigCategoryDropdownView
from modules.otterbot.utils.embeds import otter_embed


class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="config", description="Configure the bot")
    @commands.has_permissions(manage_guild=True)

    async def config(self, interaction: disnake.ApplicationCommandInteraction, plugin: str):
        # Imports an Otter Bot Plugin
        otter_plugin = importlib.import_module(f"modules.{plugin}.configurations")
        available_categories = otter_plugin.get_config_categories()
        self.view = ConfigCategoryDropdownView(interaction, available_categories, otter_plugin)
        config_menu = self.view
        embed = otter_embed(interaction.author)
        embed.title = "Configure the bot"
        embed.description = "Select an category to configure the bot."
        embed.add_field(name="Available categories", value="\n".join(available_categories))
        await interaction.response.send_message(embed=embed, view=config_menu)

    @config.autocomplete("plugin")
    async def autocomplete_plugins(self, interaction: disnake.ApplicationCommandInteraction, user_input: str) -> List[str]:
        string = user_input.lower()
        return [plugins for plugins in self.bot.loaded_plugins if string in plugins.lower() and plugins != "otterbot"]

    # @commands.slash_command(name="change_user", description="Change the bot's Status, Name or Avatar")
    # @commands.has_permissions(manage_guild=True)
    # async def change_user(self):
    #     pass
    #
    # @change_user.sub_command(name="change_user_pfp", description="Change the bot's avatar")
    # @commands.has_permissions(manage_guild=True)
    # async def change_avatar(self, interaction: disnake.CommandInteraction):
    #     await interaction.response.send_message("Soon")


def setup(bot):
    bot.add_cog(ConfigCog(bot))
