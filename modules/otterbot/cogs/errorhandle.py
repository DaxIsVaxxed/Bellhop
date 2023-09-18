import disnake
from disnake.ext import commands

from utils.sentry import log_exception


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_error_message(self, interaction, content):
        if not interaction.response.is_done():
            await interaction.response.send_message(content, ephemeral=True)
        else:
            await interaction.followup.send(content, ephemeral=True)

    @commands.Cog.listener()
    async def on_slash_command_error(self, interaction: disnake.ApplicationCommandInteraction,
                                     error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await self.send_error_message(interaction, "You don't have the required permissions to run this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await self.send_error_message(interaction, "You are missing required arguments.")
        elif isinstance(error, commands.BadArgument):
            await self.send_error_message(interaction, "You provided an invalid argument.")
        elif isinstance(error, commands.CommandOnCooldown):
            await self.send_error_message(interaction, f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
        elif isinstance(error, commands.CommandInvokeError):
            log_exception(interaction.bot, error, interaction)
            await self.send_error_message(interaction, f"An unknown error occurred.\n{error}")
        else:
            log_exception(interaction.bot, error, interaction)
            await self.send_error_message(interaction, "An unknown error occurred.")
            raise error


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
