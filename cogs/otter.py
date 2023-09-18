import disnake
from disnake.ext import commands

from main import OtterClient


class TestCog(commands.Cog):
    def __init__(self, bot: OtterClient):
        self.bot = bot

    @commands.slash_command(name='otters')
    async def otter(self, interaction: disnake.AppCommandInteraction):
        await interaction.response.send_message('OTTERSS!')



def setup(bot):
    bot.add_cog(TestCog(bot))
