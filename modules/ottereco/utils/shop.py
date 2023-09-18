from disnake.ui import Select
import disnake
from disnake import SelectOption
from modules.ottereco.database.model import EconomyGuild, EconomyUser, PurchasableRole

from modules.ottereco.utils.embeds import eco_log, otter_embed
from modules.ottereco.utils.helpers import format_money, send_log

class ShopDropDown(Select):
    def __init__(self, options: list[SelectOption] | None):
        super().__init__(
            custom_id="shop_dropdown",
            placeholder="Select a role to purchase",
            options=options or [],
        )

    async def callback(self, interaction: disnake.MessageInteraction):
        # If the user is in a guild disregard
        if not interaction.guild:
            return
        # Gets role from selected
        role = interaction.guild.get_role(int(self.values[0]))
        # Get member from interaction
        member = interaction.guild.get_member(interaction.user.id)
        # If role or member is None disregard
        if not role or not member:
            return
        # If the user has the role already make/send embed saying they already have it
        if member.roles.__contains__(role):
            embed = otter_embed(interaction.author)
            embed.title = "Error"
            embed.description = "You already have this role!"
            embed.color = disnake.Colour.red()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Gets role from database
        role_schema = await PurchasableRole.fetch(guild_id=interaction.guild.id, role_id=role.id)
        # Gets guild data
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        # Gets the user data
        user_schema = await EconomyUser.fetch(user_id=interaction.user.id, guild_id=interaction.guild.id)
        # If the user cannot afford the role, make/send the embed saying they cannot afford it
        if user_schema.balance < role_schema.price:
            embed = otter_embed(interaction.author)
            embed.title = "Error"
            embed.description = "You do not have enough money to purchase this role!"
            embed.color = disnake.Colour.red()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Take the money from the user and give them the role
        user_schema.balance -= role_schema.price
        # Save the user data
        await user_schema.save()
        await member.add_roles(role)
        # Makes/send embed saying they purchased the role
        embed = otter_embed(interaction.author)
        embed.title = "Purchased Role"
        embed.description = f"You have purchased the role {role.mention} for {format_money(role_schema.price, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}"
        embed.color = disnake.Colour.green()
        await interaction.response.send_message(embed=embed, ephemeral=True)
        # If logs are not set, disregard
        if guild_schema.economy_log_channel is None:
            return
        # Sends the logs
        log = eco_log(interaction.author)
        await send_log(interaction, log, "Purchased Role", f"{interaction.author.mention} bought the role {role.mention} for {format_money(role_schema.price, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}")
        


class ShopDropDownView(disnake.ui.View):
    def __init__(self, options: list[SelectOption] | None = None):
        super().__init__(timeout=None)

        self.add_item(ShopDropDown(options))
