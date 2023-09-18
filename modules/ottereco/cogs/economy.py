import copy
import io
from datetime import datetime, timedelta
import math
import random
from typing import Optional
import disnake
from disnake import Client, SelectOption
from apgorm.exceptions import ModelNotFound
from disnake.ext import commands
import apgorm
from modules.ottereco.database.model import PurchasableRole, EconomyGuild, EconomyRoleIncome, EconomyRoleMultplier, EconomyUser
from modules.ottereco.utils.embeds import otter_embed, eco_log

from modules.ottereco.utils.helpers import economy_enabled, format_money, send_log
from modules.ottereco.utils.shop import ShopDropDownView


async def autocomp_purchasable_roles(inter: disnake.ApplicationCommandInteraction, user_input: str):
    # If not in a guild disregard
    if inter.guild is None:
        return
    # Get role data from database
    role_schema = await PurchasableRole.get_all_by_gid(guild_id=inter.guild.id)
    # creates empty list
    roles = []
    # for each role in the db
    for role in role_schema:
        # get the guild data
        real_role = inter.guild.get_role(role.role_id)
        # if the role is not found disregard
        if not real_role:
            return
        # if the role name starts with the user input
        if real_role.name.lower().startswith(user_input.lower()):
            # add the role to the list
            roles.append(f"{real_role.name} (id:{real_role.id})")
    # return the list for the autocomplete
    return roles

async def autocomp_multiplier_roles(inter: disnake.ApplicationCommandInteraction, user_input: str):
    # Gets guild data
    if inter.guild is None:
        return
    # Gets role multiplier roles from database
    role_schema = await EconomyRoleMultplier.get_all_by_gid(guild_id=inter.guild.id)
    # Empty role list 
    roles = []
    # For each role in the DB
    for role in role_schema:
        # Get the role from guild 
        real_role = inter.guild.get_role(role.role_id)
        # If the role is not found disregard
        if not real_role:
            return
        # If the role name starts with the user input
        if real_role.name.lower().startswith(user_input.lower()):
            # Add the role to the list
            roles.append(f"{real_role.name} (id:{real_role.id})")
    # returns the list of roles for autocomplete
    return roles

async def autocomp_roles(inter: disnake.ApplicationCommandInteraction, user_input: str):
    # Gets guild data
    if inter.guild is None:
        return
    # Gets role perchasable roles from database
    role_schema = await PurchasableRole.get_all_by_gid(guild_id=inter.guild.id)
    # Empty role list 
    roles = []
    # For each role in the DB
    for role in role_schema:
        real_role = inter.guild.get_role(role.role_id)
        # If the role name starts with the user input
        if real_role and real_role.name.lower().startswith(user_input.lower()):
            # Add the role to the list
            roles.append(f"{real_role.name} (id:{real_role.id})")
    # returns the list of roles for autocomplete
    return roles

async def autocomp_role_income(inter: disnake.ApplicationCommandInteraction, user_input: str):
    # Gets guild data
    if inter.guild is None:
        return
    # Gets role income roles from database
    role_schema = await EconomyRoleIncome.get_all_by_gid(guild_id=inter.guild.id)
    # Empty role list 
    roles = []
    # For each role in DB
    for role in role_schema:
        if role.role_id is None:
            continue
        real_role = inter.guild.get_role(role.role_id)
        # If the role name starts with the user input
        if real_role and real_role.name.lower().startswith(user_input.lower()):
            # Add the role to the list
            roles.append(f"{real_role.name} (id:{real_role.id})")
    # returns the list of roles for autocomplete
    return roles


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command()
    @economy_enabled()
    @commands.has_permissions(manage_guild=True)
    async def manage_shop(self, interaction: disnake.GuildCommandInteraction):
        # Subcommand group for managing the shop
        pass

    @manage_shop.sub_command()
    @economy_enabled()
    @commands.has_permissions(manage_guild=True)
    async def update_price(self, interaction: disnake.GuildCommandInteraction, role: disnake.Role, price: int):
        """
        Update the price of a role in the shop

        Parameters
        ----------
        role: The role to update the price of
        price: The new price of the role
        """
        # Gets guild data
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        try:
            # Gets role data
            role_schema = await PurchasableRole.fetch(guild_id=interaction.guild.id, role_id=role.id)
        except ModelNotFound:
            # If role is not in the shop make/send embed saying it is not in the shop
            embed = otter_embed(interaction.author)
            embed.title = "Role not in shop"
            embed.description = f"{role.mention} is not in the shop"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Sets the price of the role to the new price
        role_schema.price = price
        # Saves it into the database
        await role_schema.save()
        # Make/sends the embed saying the price has been updated
        embed = otter_embed(interaction.author)
        embed.title = "Price updated"
        embed.description = f"Updated the price of {role.mention} to {price}"
        await interaction.response.send_message(embed=embed, ephemeral=True)
        # Logs it
        log_embed = eco_log(interaction.author)
        await send_log(interaction, log_embed, "Updated price of role in shop", f"{interaction.user} has updated the price of {role.mention} to {format_money(price, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}")
        return

    @manage_shop.sub_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def add_role(self, interaction: disnake.GuildCommandInteraction, role: disnake.Role, price: int):
        """
        Add a role to the shop

        Parameters
        ----------
        role: The role to add to the shop
        price: The price of the role
        """
        # Get guild data
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        try:
            # attempts to get the role from the dabatase
            await PurchasableRole.fetch(guild_id=interaction.guild.id, role_id=role.id)
        except ModelNotFound:
            # If not found make one and make/send embed for it
            await PurchasableRole(guild_id=interaction.guild.id, role_id=role.id, price=price).create()
            embed = otter_embed(interaction.author)
            embed.title = "Role added to shop"
            embed.description = f"Added {role.mention} to the shop for {format_money(price, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # If it's already in the shop then make/send embed saying it is
        embed = otter_embed(interaction.author)
        embed.title = "Role already in shop"
        embed.description = f"{role.mention} is already in the shop"
        await interaction.response.send_message(embed=embed, ephemeral=True)
        # Logs it
        log_embed = eco_log(interaction.author)
        await send_log(interaction, log_embed, "Added role to shop", f"{interaction.user} has added the role {role.mention} for {price}")

        return

    @manage_shop.sub_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def remove_role(self, interaction: disnake.GuildCommandInteraction,
                          role: str = commands.Param(autocomplete=autocomp_purchasable_roles)):
        """
        Remove a role from the shop

        Parameters
        ----------
        role: The role to remove from the shop
        """
        # Gets the role id from the automcomp
        role_id = int(role.split("id:")[1].split(")")[0])
        try:
            # Gets the role from the database
            role_schema = await PurchasableRole.fetch(guild_id=interaction.guild.id, role_id=role_id)
        except ModelNotFound:
            # If not found then make/send embed saying it is not in the shop
            embed = otter_embed(interaction.author)
            embed.title = "Role not in shop"
            embed.description = f"{role} is not in the shop"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Get the role from the guild
        guild_role = interaction.guild.get_role(role_id)
        if guild_role is None:
            # If not found then make/send embed saying it is not in the guild
            embed = otter_embed(interaction.author)
            embed.title = "Role not in guild"
            embed.description = f"{role} is no longer existing in the guild"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Get role data
        role_schema = await PurchasableRole.fetch(guild_id=interaction.guild.id, role_id=guild_role.id)
        # delete the role data
        await role_schema.delete()
        # Make/send the embed saying it has been removed
        embed = otter_embed(author=interaction.author)
        embed.title = "Role removed from shop"
        embed.description = f"Role {guild_role.name} removed from shop"
        await interaction.response.send_message(embed=embed, ephemeral=True)
        # Logs it
        log_embed = eco_log(interaction.author)
        await send_log(interaction, log_embed, "Removed role from shop", f"{interaction.user} has removed the role {guild_role.mention} from the shop")
        return

    @manage_shop.sub_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def list_roles(self, interaction: disnake.GuildCommandInteraction):
        """
        List all roles in the shop
        """
        # Gets the guild data
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        # Gets all roles from the database for the guild
        query = PurchasableRole.fetch_query().where(
            PurchasableRole.guild_id.eq(interaction.guild.id))
        roles = await query.fetchmany()
        # If there are no roles make/send embed saying there are no roles
        if len(roles) == 0:
            embed = otter_embed(interaction.author)
            embed.title = "No roles in shop"
            embed.description = "There are no roles in the shop"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Make/send embed with all the roles
        embed = otter_embed(interaction.author)
        embed.title = "Shop roles"
        embed.description = ""
        # For each roles
        for role in roles:
            # Get the role from the guild
            real_role = interaction.guild.get_role(role.role_id)
            if real_role is None:
                continue
            # Add the role to the embed with the price formatted
            embed.description += f"{real_role.name} - {format_money(role.price, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}\n"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @manage_shop.sub_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def send_shop(self, interaction: disnake.GuildCommandInteraction, channel: disnake.TextChannel | None = None):
        """
        Sends the shop message
        """
        await interaction.response.defer()
        # If channel doesn't exist use the interaction channel
        if channel is None:
            # Checks if channel is a text channel
            if isinstance(interaction.channel, disnake.TextChannel):
                channel = interaction.channel
            else:
                # Otherwise makes/send embed saying it is not a text channel
                embed = otter_embed(interaction.author)
                embed.title = "No channel specified"
                embed.description = "You must specify a channel to send the shop to"
                await interaction.edit_original_response(embed=embed)
                return
        # gets guild data
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        # gets all the roles from the database for the guild
        purchasable_roles = await PurchasableRole.get_all_by_gid(guild_id=interaction.guild.id)
        # if there are no roles make/send embed saying there are no roles
        if len(purchasable_roles) == 0:
            embed = otter_embed(interaction.author)
            embed.title = "No roles in shop"
            embed.description = "There are no roles in the shop"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Otherwise make/send embed with all the roles
        shop_embed = otter_embed(interaction.author)
        shop_embed.title = "Shop"
        shop_embed.description = "Use the dropdown below to purchase a role"
        options: list[SelectOption] = []
        # For each role
        for role in purchasable_roles:
            # Get the role from the guild
            guild_role = interaction.guild.get_role(role.role_id)
            # If the role is not found disregard
            if guild_role is None:
                continue
            # Add the role to the dropdown to perchase
            options.append(SelectOption(label=f"{guild_role.name} ({format_money(role.price, guild_schema.economy_currency, guild_schema.economy_currency_on_left)})", value=f"{guild_role.id}"))
            shop_embed.add_field(name=guild_role.name, value=f"{format_money(role.price, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}", inline=False)
        # Send the shop message with the shopdrop down
        shop_message = await channel.send(embed=shop_embed, view=ShopDropDownView(options))    
        await interaction.edit_original_response(f"Shop sent in {shop_message.jump_url}")
            


    @commands.slash_command()
    @economy_enabled()
    async def balance(self, interaction: disnake.GuildCommandInteraction, user: disnake.Member | None = None):
        """
            Shows your or other's balance
        """
        # If user is not provided, use the interaction author
        if user is None:
            user = interaction.guild.get_member(interaction.author.id)
            if user is None:
                # If the user is not in the guild make/send embed saying they are not in the guild
                return await interaction.response.send_message("You are not in this server. (For some reason??)", ephemeral=True)
        # Get user and guild data
        user_schema = await EconomyUser.fetch(user_id=user.id, guild_id=interaction.guild.id)
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        # Makes/send embed with the balance
        embed = otter_embed(interaction.author)
        embed.title = f"{user.name}'s Balance"
        embed.description = f"**Balance:** {format_money(user_schema.balance, guild_schema.economy_currency, guild_schema.economy_currency_on_left)} "
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def add_money(self, interaction: disnake.GuildCommandInteraction, user: disnake.User, amount: int):
        """
        Add money to a user

        Parameters
        ----------
        user: The user to add money to
        amount: Money to add
        """
        # Get user and guild data
        user_schema = await EconomyUser.fetch(user_id=user.id, guild_id=interaction.guild.id)
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        # Update the balance with the amount provided
        user_schema.balance += amount
        # Saves it to the database
        await user_schema.save()
        # Make/send the embed saying it added the money
        embed = otter_embed(interaction.author)
        embed.title = "Money added"
        embed.description = f"Added {format_money(amount, guild_schema.economy_currency, guild_schema.economy_currency_on_left)} to {user.mention}"
        await interaction.response.send_message(embed=embed, ephemeral=True)
        # Logs it
        eco_log_embed = eco_log(interaction.author)
        eco_log_embed.title = "Money added"
        eco_log_embed.description = f"Added {format_money(amount, guild_schema.economy_currency, guild_schema.economy_currency_on_left)} to {user.mention} (By {interaction.user})"
        await send_log(interaction, eco_log_embed, "Money added", f"{interaction.user} has added {format_money(amount, guild_schema.economy_currency, guild_schema.economy_currency_on_left)} to {user.mention}")

    @commands.slash_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def remove_money(self, interaction: disnake.GuildCommandInteraction, user: disnake.User, amount: int):
        """
        Remove money from a user

        Parameters
        ----------
        user: The user to remove money from
        """
        # Gets user and guild data
        user_schema = await EconomyUser.fetch(user_id=user.id, guild_id=interaction.guild.id)
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        # Takes the money from the user
        user_schema.balance -= amount
        # Saves it to the databse
        await user_schema.save()
        # Makes/send the embed saying it removed the money
        embed = otter_embed(interaction.author)
        embed.title = "Money removed"
        embed.description = f"Removed {format_money(amount, guild_schema.economy_currency, guild_schema.economy_currency_on_left)} from {user.mention}"
        # Logs it
        eco_log_embed = eco_log(interaction.author)
        eco_log_embed.title = "Money removed"
        eco_log_embed.description = f"Removed {format_money(amount, guild_schema.economy_currency, guild_schema.economy_currency_on_left)} from {user.mention} (By {interaction.user})"
        await send_log(interaction, eco_log_embed, "Removed money from user", f"{interaction.user} has removed {format_money(amount, guild_schema.economy_currency, guild_schema.economy_currency_on_left)} from {user.mention}")
        return await interaction.response.send_message(embed=embed, ephemeral=True)
        

    @commands.slash_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def roles_income(self, interaction: disnake.GuildCommandInteraction):
        # Sub grouo
        pass

    @roles_income.sub_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def add_income(self, interaction: disnake.GuildCommandInteraction, role: disnake.Role, min: int, max: int):
        """
        Add a role to the roles income

        Parameters
        ----------
        role: Role to add to the roles income
        min: Minimum amount of money to give to a user
        max: Maximum amount of money to give to a user
        """
        # Gets the guild data
        guild_data = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        try:
            # Attempts to get the role from the database
            await EconomyRoleIncome.fetch(guild_id=interaction.guild.id, role_id=role.id)
        except ModelNotFound:
            # If not found make one and make/send embed for it
            await EconomyRoleIncome(guild_id=interaction.guild.id, role_id=role.id, min_income=min,
                                    max_income=max).create()
            embed = otter_embed(interaction.author)
            embed.title = "Role added to roles income"
            embed.description = f"Added {role.mention} to the roles income with a minimum of {format_money(min, guild_data.economy_currency, guild_data.economy_currency_on_left)} and a maximum of {format_money(max, guild_data.economy_currency, guild_data.economy_currency_on_left)} per day"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Sends embed saying it is already in the roles income
        embed = otter_embed(interaction.author)
        embed.title = "Role already in roles income"
        embed.description = f"{role.mention} is already in the roles income"
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    @roles_income.sub_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def remove_income(self, interaction: disnake.GuildCommandInteraction,
                     role: str = commands.Param(autocomp=autocomp_role_income)):
        """
        Remove a role from the roles income

        Parameters
        ----------
        role: Role to remove from the roles income
        """
        # Gets role id from auto complemete
        role_id = int(role.split("(id:")[1].split(")")[0])
        # Gets the role from the guild
        real_role = interaction.guild.get_role(role_id)
        # If not found make/send embed saying it's not found
        if real_role is None:
            embed = otter_embed(interaction.author)
            embed.title = "Role not found"
            embed.description = "Role not found"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            # Attempts to get the role from the database
            role_schema = await EconomyRoleIncome.fetch(guild_id=interaction.guild.id, role_id=real_role.id)
            await role_schema.delete()
        except ModelNotFound:
            # Make/sends the embed saying it's not found
            embed = otter_embed(interaction.author)
            embed.title = "Role not found"
            embed.description = "Role not found"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Make/sends the embed saying it has been removed
        embed = otter_embed(interaction.author)
        embed.title = "Role removed from roles income"
        embed.description = f"Removed {real_role.name} from the roles income"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @roles_income.sub_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def update_income(self, interaction: disnake.GuildCommandInteraction, role: disnake.Role, min: int, max: int):
        """
        Update a role in the roles income

        Parameters
        ----------
        role: Role to update in the roles income
        min: New Minimum amount of money to give to a user per day
        max: New Maximum amount of money to give to a user per day
        """
        # Gets the guild data
        guild_data = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        try:
            # Gets the role income data
            role_schema = await EconomyRoleIncome.fetch(guild_id=interaction.guild.id, role_id=role.id)
        except ModelNotFound:
            # Makes/send the embed saying it is not in the roles income
            embed = otter_embed(interaction.author)
            embed.title = "Role not in roles income"
            embed.description = f"{role.mention} is not in the roles income"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Change the min and max income based on what's provded in params
        role_schema.min_income = min
        role_schema.max_income = max
        # Saves it to the database
        await role_schema.save()
        # Makes/send embed saying it has been updated
        embed = otter_embed(interaction.author)
        embed.title = "Role updated in roles income"
        embed.description = f"Updated {role.mention} in the roles income with a minimum of {format_money(min, guild_data.economy_currency, guild_data.economy_currency_on_left)} and a maximum of {max, guild_data.economy_currency, guild_data.economy_currency_on_left} per day"
        await interaction.response.send_message(embed=embed, ephemeral=True)


    @roles_income.sub_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def list_incomes(self, interaction: disnake.GuildCommandInteraction):
        """
        List all roles in the roles income
        """
        # Gets role data
        guild_data = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        # Gets all role from the guild
        roles = await EconomyRoleIncome.get_all_by_gid(guild_id=interaction.guild.id)
        # Empty string for roles
        roleStr = ""
        # Makes the embed
        embed = otter_embed(interaction.user)
        embed.title = "Roles income"
        print(roles)
        # For each role
        for role_data in roles:
            # If it doesn't exist then disregard
            if role_data is None:
                continue
            # Get the role from the guild
            role = interaction.guild.get_role(role_data.role_id) # type: ignore
            # If role doesn't exist then disregard
            if role is None:
                continue
            # Add the role to the string with formatted money
            roleStr += f"{role.mention}: {format_money(role_data.min_income, guild_data.economy_currency, guild_data.economy_currency_on_left)} - {format_money(role_data.max_income, guild_data.economy_currency, guild_data.economy_currency_on_left)}\n"
        # If the string wasn't touched then say there's nothing in the databse
        if roleStr == "":
            roleStr = "No roles in the database"
        # Set description to the final string and send it
        embed.description = roleStr
        await interaction.response.send_message(embed=embed)

    @commands.slash_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def set_balance(self, interaction: disnake.GuildCommandInteraction, user: disnake.User, amount: int):
        """
        Set a user's balance

        Parameters
        ----------
        user: The user to set the balance of
        amount: The amount to set the balance to
        """
        # Get user and guild data
        user_schema = await EconomyUser.fetch(user_id=user.id)
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        # Set the balance to the amount provided
        user_schema.balance = amount
        # Save it in the databse
        await user_schema.save()
        # Makes/send the embed saying it has been set
        embed = otter_embed(interaction.author)
        embed.title = "Balance set"
        embed.description = f"Set {user.mention}'s balance to {format_money(amount, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def role_multiplier(self, interaction: disnake.GuildCommandInteraction):
        # Sub grouo
        pass

    @role_multiplier.sub_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def add_multiplier(self, interaction: disnake.GuildCommandInteraction, role: disnake.Role, multiplier: float):
        """
        Add a role to the role multiplier

        Parameters
        ----------
        role: Role to add to the role multiplier
        multiplier: The multiplier to give to the role
        """
        try:
            # Attempts to get the role multiplier
            await EconomyRoleMultplier.fetch(role_id=role.id)
        except ModelNotFound:
            # If not found make one and make/send embed for it
            await EconomyRoleMultplier(guild_id=role.guild.id, role_id=role.id, multiplier=multiplier).create()
            embed = otter_embed(interaction.author)
            embed.title = "Role added to role multiplier"
            embed.description = f"Added {role.mention} to the role multiplier with a multiplier of {multiplier}"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Otherwise make/send embed saying it is already in the role multiplier
        embed = otter_embed(interaction.author)
        embed.title = "Role already in role multiplier"
        embed.description = f"{role.mention} is already in the role multiplier"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @role_multiplier.sub_command()
    @commands.has_permissions(manage_guild=True)
    @economy_enabled()
    async def remove_multiplier(self, interaction: disnake.GuildCommandInteraction,
                     role: str = commands.Param(autocomp=autocomp_multiplier_roles)):
        """
        Remove a role from the role multiplier
        """
        # Get role from the autocomp
        role_id = int(role.split("(id:")[1].split(")")[0])
        real_role = interaction.guild.get_role(role_id)
        if real_role is None:
            return
        try:
            # Attempt to get the role from the database
            role_schema = await EconomyRoleMultplier.fetch(role_id=real_role.id)
        except ModelNotFound:
            # Make/send embed saying it is not in the role multiplier
            embed = otter_embed(interaction.author)
            embed.title = "Role not in role multiplier"
            embed.description = f"{real_role.mention} is not in the role multiplier"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Delete the role from the database
        await role_schema.delete()
        # Makes/send embed saying it has been removed
        embed = otter_embed(interaction.author)
        embed.title = "Role removed from role multiplier"
        embed.description = f"Removed {real_role.mention} from the role multiplier"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command()
    @economy_enabled()
    async def roleshop(self, interaction: disnake.GuildCommandInteraction):
        # Another sub group
        pass

    @roleshop.sub_command()
    @economy_enabled()
    async def list(self, interaction: disnake.GuildCommandInteraction):
        """
        List all roles in the shop
        """
        # Get roles from the database
        roles = await PurchasableRole.get_all_by_gid(guild_id=interaction.guild.id)
        # Get guild data
        guild_data = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        # Make/send embed for the list``
        embed = otter_embed(interaction.author)
        embed.title = "Role Shop"
        embed.description = ""
        # If no roles then put that there are no roles
        if len(roles) == 0:
            embed.color = disnake.Colour.red()
            embed.description = "No roles in the shop, Ask a server administrator to add some."
            return await interaction.response.send_message(embed=embed)
        # For each role, update the embed description with the role and price
        for roleData in roles:
            role = interaction.guild.get_role(roleData.role_id)
            if role is None:
                continue
            embed.description += f"{role.name} - {format_money(roleData.price, guild_data.economy_currency, guild_data.economy_currency_on_left)}\n"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @roleshop.sub_command()
    @economy_enabled()
    async def buy(self, interaction: disnake.GuildCommandInteraction,
                  role: str = commands.Param(autocomplete=autocomp_roles)):
        """
        Buy a role from the shop

        Parameters
        ----------
        role: The role to buy
        """
        # Gets member
        member: disnake.Member = interaction.guild.get_member(
            interaction.user.id)  # type: ignore
        # Gets the role id from the autocomplete
        role_id = int(role.split("(id:")[1].split(")")[0])
        purchasing_role = interaction.guild.get_role(role_id)
        # If the role doesn't exist anymore make/send embed saying it doesn't exist
        if purchasing_role is None:
            embed = otter_embed(interaction.author)
            embed.title = "Error"
            embed.description = "The role doesn't exist anymore"
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        # If the member already has the role make/send embed saying they already have it
        if member.roles.__contains__(purchasing_role):
            embed = otter_embed(interaction.author)
            embed.title = "Error"
            embed.description = "You already have this role!"
            embed.color = disnake.Colour.red()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Get role, guild and user data
        role_schema = await PurchasableRole.fetch(guild_id=interaction.guild.id, role_id=role_id)
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        user_schema = await EconomyUser.fetch(user_id=interaction.user.id, guild_id=interaction.guild.id)
        # If the user doesn't have enough money make/send embed saying they don't have enough money
        if user_schema.balance < role_schema.price:
            embed = otter_embed(interaction.author)
            embed.title = "Error"
            embed.description = f"You don't have enough money to buy this role! You need {format_money(role_schema.price, guild_schema.economy_currency, guild_schema.economy_currency_on_left)} but you only have {format_money(user_schema.balance, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}"
            embed.color = disnake.Colour.red()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Take away the money and give the role
        user_schema.balance -= role_schema.price
        await user_schema.save()
        await member.add_roles(purchasing_role)
        # Make/send embed saying it has been bought
        embed = otter_embed(interaction.author)
        embed.title = "Purchased Role"
        embed.color = disnake.Colour.green()
        embed.description = f"You have successfully bought the role {purchasing_role.name} for {format_money(role_schema.price, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}"
        await interaction.response.send_message(embed=embed, ephemeral=True)
        if guild_schema.economy_log_channel is None:
            return
        # Logs it if channel is configured
        log = eco_log(interaction.author)
        await send_log(interaction, log, "Purchased Role", f"{interaction.author.mention} bought the role {purchasing_role.mention} for {format_money(role_schema.price, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}")
        return
    
    @commands.slash_command()
    @economy_enabled()
    async def claim(self, interaction: disnake.GuildCommandInteraction):
        """
        Claim your daily reward
        """
        # Money to add to the user per role
        temp = 0
        # Gets user and guild data
        user_schema = await EconomyUser.fetch(user_id=interaction.user.id, guild_id=interaction.guild.id)
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        # If the daily reward is avaliable
        if user_schema.last_role_income is not None:
            # Check if the last time it was claimed was today
            if user_schema.last_role_income == datetime.now().date():
                # Makes/send embed saying it has already been claimed
                embed = otter_embed(interaction.author)
                embed.title = "Error"
                embed.description = f"You have already claimed your daily role income! You can claim it again later"
                embed.color = disnake.Colour.red()
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        # Sets the time to today
        user_schema.last_role_income = datetime.utcnow()
        # Get all roles from the database
        roles = await EconomyRoleIncome.get_all_by_gid(guild_id=interaction.guild.id)
        # Go through all the roles
        for role in roles:
            # If the role doesn't exist then disregard
            if role.role_id is None:
                continue
            # If the role doesn't exist in the guild then disregard
            if interaction.guild.get_role(role.role_id) is None:
                continue
            # If it does
            if interaction.guild.get_role(role.role_id) in interaction.author.roles:
                # Set the temp to a random number between the min and max income
                temp += random.randint(role.min_income, role.max_income)    
        # Add total to the user's balance    
        user_schema.balance += temp
        # Saves it to the database
        await user_schema.save()
        # Make/sends embed saying it has been claimed
        embed = otter_embed(interaction.author)
        embed.title = "Role Income"
        embed.description = f"You have claimed your role income of {format_money(temp, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}"
        embed.color = disnake.Colour.green()
        await interaction.response.send_message(embed=embed, ephemeral=True)
        if guild_schema.economy_log_channel is None:
            return
        # Logs it if the channel is configured
        log = eco_log(interaction.author)
        await send_log(interaction, log, "Role Income", f"{interaction.author.mention} claimed their daily role income of {format_money(temp, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}")
        return

    @commands.slash_command()
    @economy_enabled()
    async def work(self, interaction: disnake.GuildCommandInteraction):
        """
        Claim your daily work reward
        """
        # Get user and guild data
        user_schema = await EconomyUser.fetch(user_id=interaction.user.id, guild_id=interaction.guild.id)
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        # If the work is configured wrong then make/send embed saying it is and a server admin needs to fix it
        if guild_schema.economy_work_amount_min > guild_schema.economy_work_amount_max:
            embed = otter_embed(interaction.author)
            embed.title = "Error"
            embed.description = "The minimum work amount is higher than the maximum work amount, Please ask a server administrator to fix this."
            embed.color = disnake.Colour.red()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # If both min/max are 0 consider it disabled make/send embed saying it is
        if guild_schema.economy_work_amount_min == 0 or guild_schema.economy_work_amount_max == 0:
            embed = otter_embed(interaction.author)
            embed.title = "Error"
            embed.description = "Earning from work is disabled."
            embed.color = disnake.Colour.red()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # If the last time they worked was not today
        if user_schema.last_work != datetime.now().date():
            # Set the income to a random number between the min and max work amount
            income = random.randint(
                guild_schema.economy_work_amount_min, guild_schema.economy_work_amount_max)
            # Makes/Send embed saying they worked and how much they earned
            embed = otter_embed(interaction.author)
            embed.title = f"Paycheck from work!"
            embed.description = f"You worked today and gained {format_money(income, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}"
            # Updates the last time they worked and adds the income to their balance
            user_schema.last_work = datetime.now().date()
            user_schema.balance += income
            await user_schema.save()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            # Logs it
            log = eco_log(interaction.author)
            await send_log(interaction, log, "Income from Work", f"{interaction.author.mention} worked and gained {format_money(income, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}")
            return
        # Otherise make/send embed saying they already worked today
        embed = otter_embed(interaction.author)
        embed.title = "You have already worked today!"
        embed.description = "Come back tomorrow!"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command()
    @economy_enabled()
    async def daily(self, interaction: disnake.GuildCommandInteraction):
        """
        Claim your daily reward
        """
        # get user and guild data
        user_schema = await EconomyUser.fetch(user_id=interaction.user.id, guild_id=interaction.guild.id)
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        # If the daily income is configured wrong then make/send embed saying it is and a server admin needs to fix it
        if guild_schema.economy_daily_amount_min > guild_schema.economy_daily_amount_max:
            embed = otter_embed(interaction.author)
            embed.title = "Error"
            embed.description = "The minimum daily amount is higher than the maximum daily amount, Please ask a server administrator to fix this."
            embed.color = disnake.Colour.red()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # If both min/max are 0 consider it disabled make/send embed saying it is
        if guild_schema.economy_daily_amount_min == 0 or guild_schema.economy_daily_amount_max == 0:
            embed = otter_embed(interaction.author)
            embed.title = "Error"
            embed.description = "Earning from daily is disabled."
            embed.color = disnake.Colour.red()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Make sure they haven't already claimed their daily
        if user_schema.last_daily != datetime.now().date():
            # Sets their last daily to today
            user_schema.last_daily = datetime.now().date()
            # Updates balance
            user_schema.balance += random.randint(guild_schema.economy_message_earnings_min,
                                                  guild_schema.economy_message_earnings_max)
            # Saves to database
            await user_schema.save()
            # Makes/send embed saying they claimed their daily and how much they earned
            embed = otter_embed(interaction.author)
            embed.title = "You claimed your daily!"
            embed.description = f"You now have {format_money(user_schema.balance, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            # logs it
            log = eco_log(interaction.author)
            await send_log(interaction, log, "Daily Income", f"{interaction.author.mention} claimed their daily and gained {format_money(user_schema.balance, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}")
            return
        # Otherwise make/send embed saying they already claimed their daily
        embed = otter_embed(interaction.author)
        embed.title = "Daily Income!"
        embed.description = "Come back tomorrow for more!"
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    @commands.slash_command()
    @economy_enabled()
    async def give(self, interaction: disnake.GuildCommandInteraction, user: disnake.User, amount: int):
        """
        Give money to another user

        Parameters
        ----------
        user: User you're wanting to give money to
        amount: Amount of money you're wanting to give
        """
        # If the user is a bot make/send embed saying you can't give money to a bot
        if user.bot:
            embed = otter_embed(interaction.author)
            embed.title = "You can't give money to a bot!"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # If the user is yourself make/send embed saying you can't give money to yourself
        if user == interaction.user:
            embed = otter_embed(interaction.author)
            embed.title = "You can't give yourself money!"
            embed.description = "You can't give yourself money!"
        # Get user, target, and guild data
        user_schema = await EconomyUser.fetch(user_id=interaction.user.id, guild_id=interaction.guild.id)
        guild_schema = await EconomyGuild.fetch(guild_id=interaction.guild.id)
        target_schema = await EconomyUser.fetch(user_id=user.id, guild_id=interaction.guild.id)
        # If the user doesn't have enough money make/send embed saying they don't have enough money
        if user_schema.balance < amount:
            embed = otter_embed(interaction.author)
            embed.title = "You don't have enough money to give!"
            embed.description = f"You only have {format_money(user_schema.balance, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Exchange money
        user_schema.balance -= amount
        target_schema.balance += amount
        # Save both user's database
        await user_schema.save()
        await target_schema.save()
        # Makes an embed saying that the money has been given
        embed = otter_embed(interaction.author)
        embed.title = f"You gave {format_money(amount, guild_schema.economy_currency, guild_schema.economy_currency_on_left)} to {user.name}"
        embed.description = f"**{user.name}** now has {format_money(target_schema.balance, guild_schema.economy_currency, guild_schema.economy_currency_on_left)}"
        await interaction.response.send_message(embed=embed, ephemeral=True)
        # Logs it
        log = eco_log(interaction.author)
        await send_log(interaction, log, "Money Given", f"{interaction.author.mention} gave {format_money(amount, guild_schema.economy_currency, guild_schema.economy_currency_on_left)} to {user.mention}")


    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        # Gets the guild data
        guild_data = await EconomyGuild.fetch(guild_id=member.guild.id)
        try:
            # Attempts to get the user data
            user_data = await EconomyUser.fetch(user_id=member.id, guild_id=member.guild.id)
        except apgorm.exceptions.ModelNotFound:
            # Otherwise create it
            user_data = await EconomyUser(user_id=member.id, guild_id=member.guild.id, balance=guild_data.economy_starting_balance).create()
        # Logs it
        log = eco_log(member)
        log.title = "Joining Income"
        log.description = f"{member.mention} has joined the server and earned {format_money(guild_data.economy_starting_balance, guild_data.economy_currency, guild_data.economy_currency_on_left)}! (Starting Balance)"
        await send_log(member, log, "Joining Income", f"{member.mention} has joined the server and earned {format_money(guild_data.economy_starting_balance, guild_data.economy_currency, guild_data.economy_currency_on_left)}! (Starting Balance)")
        return

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        # If user bot then disregard
        if message.author.bot:
            return
        # If not in guild then disregard
        if message.guild is None:
            return
        # Get member from guild
        member = message.guild.get_member(message.author.id)
        # If member doesn't exist then disregard
        if not member:
            return
        # Get guild data
        guild_data = await EconomyGuild.fetch(guild_id=message.guild.id)
        # If economy is disabled then disregard
        if not guild_data.economy_enabled:
            return
        try:
            # Gets user data
            user_data = await EconomyUser.fetch(user_id=message.author.id, guild_id=message.guild.id)
        except apgorm.exceptions.ModelNotFound:
            # If not found then create it
            user_data = await EconomyUser(user_id=message.author.id, guild_id=message.guild.id, balance=guild_data.economy_starting_balance).create()
        # If user is not in the cooldowns then add them
        if self.bot.economy_cooldowns.get(message.author.id) is None:
            self.bot.economy_cooldowns[message.author.id] = 0
        # If the user exceeds the max messages per min then disregard
        if self.bot.economy_cooldowns[message.author.id] >= guild_data.economy_earnable_messages_per_min:
            return
        # Adds it for the cooldown
        self.bot.economy_cooldowns[message.author.id] += 1
        # Random number between min and max message income
        income = random.randint(
            guild_data.economy_message_earnings_min, guild_data.economy_message_earnings_max)
        # Sets multiplier to 1.0
        multiplier = 1.0
        # For each role
        for role in member.roles:
            try:
                # Check if the multiplier exists for that role
                role_data = await EconomyRoleMultplier.fetch(guild_id=message.guild.id, role_id=role.id)
            except apgorm.exceptions.ModelNotFound:
                # Disregard if not
                continue
            # If the role data doesn't exist then disregard
            if role_data is None:
                continue
            # It it onto the multiplier
            multiplier += role_data.multiplier
        # Add it onto the multiplier
        income = int(income * multiplier)
        # Update the balance
        user_data.balance += income
        # Saves it to the database
        await user_data.save()
        # Logs it 
        self.bot.log.info(f"{message.author} earned {format_money(income, guild_data.economy_currency, guild_data.economy_currency_on_left)} from message") # type: ignore
        log = eco_log(message.author)
        log.title = "Message Income"
        log.description = f"{message.author.mention} earned {format_money(income, guild_data.economy_currency, guild_data.economy_currency_on_left)} from a message"
        await send_log(message, log, "Message Income", f"{message.author.mention} earned {format_money(income, guild_data.economy_currency, guild_data.economy_currency_on_left)} from a message")
        return


def setup(bot: commands.Bot):
    bot.add_cog(EconomyCog(bot))
