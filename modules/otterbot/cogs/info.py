import pkg_resources
import disnake
from disnake.ext import commands



class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.slash_command(name='ping')
    async def ping(self, interaction: disnake.AppCommandInteraction):
        embed = disnake.Embed(
            title="Pong!",
            description=f"{interaction.user.mention}!",
            color=self.bot.color
        )
        embed.add_field("Bot Latency: ", f"{interaction.client.latency * 1000:.0f}ms")
        await interaction.response.send_message('Pong!')

    @commands.slash_command(name='info')
    async def info(self, interaction: disnake.AppCommandInteraction):
        await interaction.response.send_message('This is a test.')

    @commands.slash_command(name='changelog')
    async def changelog(self, interaction: disnake.AppCommandInteraction):
        # Makes an embed with the latest changelog based on the changelog.md file
        embed = disnake.Embed(
            title="Changelog",
            description="Here is the latest changelog.",
            color=self.bot.color
        )
        with open("CHANGELOG.md", "r") as changelog:
            latest_grabbed = False
            value = ""
            section = None
            sections = []
            line_number = 0
            for line in changelog.readlines():
                line_number += 1
                # Grab the very first line that starts with ## and add it as a title
                if not latest_grabbed:
                    if line.startswith("## "):
                        latest_grabbed = True
                        embed.title = line.strip("## ")
                elif line.startswith("### "):
                    # Go through the bullets of the section and add them to the value variable. Stop when you reach
                    # the next section
                    section = line.strip("### ")
                    sections.append(line)
                    value = ""
                    counter = 0
                    done = False
                    with open("CHANGELOG.md", "r") as changelog_two:
                        for line_two in changelog_two.readlines():
                            counter += 1
                            if counter > line_number:
                                if line_two.startswith("### ") and line_two != line and line_two is not sections:
                                    done = True
                                    break
                                if line_two.startswith("- "):
                                    if not done:
                                        value += f"{line_two.strip()}\n"
                        embed.add_field(name=section, value=value, inline=False)
                elif latest_grabbed and line.startswith("## "):
                    await interaction.response.send_message(embed=embed)
                    return
                


def setup(bot):
    bot.add_cog(InfoCog(bot))
