import disnake
from disnake.ext import commands


class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="setup", description="Easily setup the bot")
    @commands.has_permissions(manage_guild=True)
    async def setup_commands(self, interaction: disnake.CommandInteraction):
        await interaction.response.send_message("Coming Soon")

def setup(bot):
    bot.add_cog(SetupCog(bot))