import json
import random

import disnake
from apgorm.exceptions import ModelNotFound
from disnake.ext import commands

from modules.otterleveling.database.model import LevelingGuild, LevelUsers, LevelRoles, LevelRoleMultplier
from modules.otterleveling.main import Leveling
from modules.otterleveling.utils.embeds import otter_embed
from modules.otterleveling.utils.helpers import convertXPToLevel, convertLevelToXP, leveling_enabled


# Auto Complete for Level Roles
async def autocomp_leveling_roles(inter: disnake.GuildCommandInteraction, user_input: str):
    # Gets all the roles for the guild
    role_schema = await LevelRoles.get_all_by_gid(guild_id=inter.guild.id)
    roles = []
    # For each role in the database
    for role in role_schema:
        # Get the role
        real_role = inter.guild.get_role(role.role_id)
        # If it's unable to get the role disregard
        if not real_role:
            continue
        # If the role name starts with the user input
        if real_role.name.lower().startswith(user_input.lower()):
            # List it in the auto complete list
            roles.append(f"{real_role.name} (id:{real_role.id})")
    # Returns the list of roles
    return roles

# Auto Complete for Level Multiplier Roles
async def autocomp_leveling_multiplier_roles(inter: disnake.GuildCommandInteraction, user_input: str):
    # Get all the roles for the guild
    role_schema = await LevelRoleMultplier.get_all_by_gid(guild_id=inter.guild.id)
    roles = []
    # Go through each multiplier role
    for role in role_schema:
        # Get the role
        real_role = inter.guild.get_role(role.role_id)
        # If it's unable to get the role disregard
        if not real_role:
            return
        # If the role name starts with the user input
        if real_role.name.lower().startswith(user_input.lower()):
            # List it in the auto complete list
            roles.append(f"{real_role.name} (id:{real_role.id})")
    # Reutrn the list of roles
    return roles

class LevelingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.slash_command(name='migrate')
    @commands.is_owner()
    async def migrate(self, interaction: disnake.GuildCommandInteraction, file: disnake.Attachment):
        """
        Migrate from another leveling system with a json file

        Parameters
        ----------
        file: json file to migrate from
        
        """
        # Gets the file from the attachment
        json_data = await file.read()
        # Decodes the file to utf-8
        json_str = json_data.decode("utf-8")
        # Loads it as a json
        data = json.loads(json_str)
        # Get the user_id and xp from the json (exported)
        for user_id, xp in data.items():
            try:
                # Attempts to get the user data
                user_data = await LevelUsers.fetch(user_id=user_id, guild_id=interaction.guild.id)
            except ModelNotFound:
                # Creates it if not found
                user_data = await LevelUsers(user_id=user_id, guild_id=interaction.guild.id).create()
            # Adds the xp to the user
            user_data.xp += xp
            await user_data.save()
        # Sends a message saying it's completed
        await interaction.response.send_message("Completed Migration!", ephemeral=True)
        
        
        
    @commands.slash_command(name="view_levels", description="Get your level")
    @leveling_enabled()
    async def view_level(self, interaction: disnake.GuildCommandInteraction, user: disnake.User| disnake.Member | None = None):
        """
        View your or other's level

        Parameters
        ----------
        user: view levels for this user
        """
        # If user is not provided, get the authors level instead
        if user is None:
            user = interaction.user
        # Gets the user and guild data from the database
        user_data = await LevelUsers.fetch(user_id=user.id, guild_id=interaction.guild.id)
        guild_data = await LevelingGuild.fetch(guild_id=interaction.guild.id)
        # Get XP -> Level
        level = convertXPToLevel(user_data.xp, guild_data.leveling_xp_base)
        # Use the level from above to get the xp to next level
        xp_to_next_level = convertLevelToXP(level + 1, guild_data.leveling_xp_base) - user_data.xp 
        # Makes the embed to send to the user containing level, xp and xp to next level
        embed = otter_embed(interaction.author)
        embed.title = f"{user.name}'s Level"
        embed.description = f"**Level:** {convertXPToLevel(user_data.xp, guild_data.leveling_xp_base)}\n**XP:** {user_data.xp}\n**XP to next level:** {xp_to_next_level}"
        # Sends the embed
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command()
    @commands.has_permissions(manage_guild=True)
    async def blacklist(self, interaction: disnake.GuildCommandInteraction):
        # This is a sub command group
        pass

    @blacklist.sub_command()
    @commands.has_permissions(manage_guild=True)
    async def add(self, interaction: disnake.GuildCommandInteraction, channel: disnake.TextChannel):
        # Gets the guild
        guild_data = await LevelingGuild.fetch(guild_id=interaction.guild.id)
        # If the guild doesn't have a blacklisted channel list, create one
        if not guild_data.leveling_blacklisted_channel:
            guild_data.leveling_blacklisted_channel = []
        # Converts the list to a normal list (Apgorm list are handled weird)
        blacklisted = list(guild_data.leveling_blacklisted_channel)
        # If the channel is already blacklisted, send a message saying it's already blacklisted
        if channel.id in blacklisted:
            embed = otter_embed(interaction.author)
            embed.title = "Channel already Blacklisted"
            embed.description = "The Channel is already blacklisted from earning xp"
            await interaction.response.send_message(embed=embed, ephemeral=True)
        # Adds it to the blacklist
        blacklisted.append(channel.id)
        # Saves the guild data
        await guild_data.save()
        # Make/Send the embed saying it's completed
        embed = otter_embed(interaction.author)
        embed.title = "Blacklist Added"
        embed.description = "This channel is blacklisted from earning xp"
        await interaction.response.send_message(embed=embed, ephemeral=True)


    @blacklist.sub_command()
    @commands.has_permissions(manage_guild=True)
    async def remove(self, interaction: disnake.GuildCommandInteraction, channel: disnake.TextChannel):
        # Gets guuild data
        guild_data = await LevelingGuild.fetch(guild_id=interaction.guild.id)
        # If the guild doesn't have a blacklisted channel list, create one
        if not guild_data.leveling_blacklisted_channel:
            guild_data.leveling_blacklisted_channel = []
        # Converts the list to a normal list (Apgorm list are handled weird)
        blacklisted = list(guild_data.leveling_blacklisted_channel)
        # If the channel is not blacklisted, send a message saying it's not blacklisted
        if channel.id not in blacklisted:
            embed = otter_embed(interaction.author)
            embed.title = "Channel not blacklisted"
            embed.description = "The Channel is already not blacklisted from earning xp"
            await interaction.response.send_message(embed=embed, ephemeral=True)
        # Removes it from the blacklist
        blacklisted.remove(channel.id)
        # Saves it in the database
        await guild_data.save()
        # Make/Sends the embed saying it's completed
        embed = otter_embed(interaction.author)
        embed.title = "Blacklist Removed"
        embed.description = "This channel is no longer blacklisted from earning xp"
        await interaction.response.send_message(embed=embed, ephemeral=True)


    @commands.slash_command()
    @leveling_enabled()
    @commands.has_permissions(manage_guild=True)
    async def level_multiplier(self, interaction: disnake.GuildCommandInteraction):
        # Another sub command group
        pass

    @level_multiplier.sub_command()
    @commands.has_permissions(manage_guild=True)
    @leveling_enabled()
    async def add_multiplier(self, interaction: disnake.GuildCommandInteraction, role: disnake.Role, multiplier: float):
        """
        Add a level multiplier role

        Parameters
        ----------
        role: role to add
        multiplier: multiplier to add
        """
        # If multiplier is less than 1.0, send a message saying it's invalid
        if multiplier < 1.0:
            embed = otter_embed(interaction.user)
            embed.title = "Invalid multiplier"
            embed.description = "The multiplier must be greater than 1.0"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            # Attempts to get the level multiplier data
            await LevelRoleMultplier.fetch(guild_id=role.guild.id, role_id=role.id)
        except ModelNotFound:
            # If not found create it and make/send an embed saying it's added
            await LevelRoleMultplier(role_id=role.id, multiplier=multiplier, guild_id=role.guild.id).create()
            embed = otter_embed(interaction.user)
            embed.title = "Level multiplier role added"
            embed.description = f"Added {role.mention} as a level multiplier role with a multiplier of {multiplier}."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # If one is found, make/send an embed saying it's already added (If it didn't throw an exception it's already added)
        embed = otter_embed(interaction.user)
        embed.title = "Role already exists"
        embed.description = "This role already has a multiplier."
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @level_multiplier.sub_command()
    @commands.has_permissions(manage_guild=True)
    @leveling_enabled()
    async def remove_multiplier(self, interaction: disnake.GuildCommandInteraction,
                     role: str = commands.Param(autocomp=autocomp_leveling_multiplier_roles)):
        """
        Remove a level multiplier role

        Parameters
        ----------
        role: role to remove
        """
        # Gets the role ID via the autocomp
        role_id = int(role.split("id:")[1].split(")")[0])
        # Gets the role from the guild
        real_role = interaction.guild.get_role(role_id)
        # If the guild doesn't have the role, send a message saying it's invalid
        if not real_role:
            embed = otter_embed(interaction.user)
            embed.title = "Invalid role"
            embed.description = "The role you provided is invalid."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            # Attempts to get the level multiplier data
            await LevelRoleMultplier.fetch(role_id=real_role.id)
        except ModelNotFound:
            # If not found, send a message saying it's not found
            embed = otter_embed(interaction.user)
            embed.title = "Role doesn't have a multiplier"
            embed.description = "This role does not have a multiplier."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # If found, delete it and send a message saying it's completed
        await LevelRoleMultplier(role_id=real_role.id).delete()
        embed = otter_embed(interaction.user)
        embed.title = "Level multiplier role removed"
        embed.description = f"Removed {real_role.mention} as a level multiplier role."
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @level_multiplier.sub_command()
    @commands.has_permissions(manage_guild=True)
    @leveling_enabled()
    async def update_multiplier(self, interaction: disnake.GuildCommandInteraction, role: str = commands.Param(autocomp=autocomp_leveling_multiplier_roles), new_multiplier: float = 1.0):
        """
        Update a level multiplier role

        Parameters
        ----------
        role: role to update
        multiplier: multiplier to update
        """
        # Get role ID from autocomp
        role_id = int(role.split("id:")[1].split(")")[0])
        # Get the role from the guild
        real_role = interaction.guild.get_role(role_id)
        # If the guild doesn't have the role, send a message saying it's invalid
        if not real_role:
            embed = otter_embed(interaction.user)
            embed.title = "Invalid role"
            embed.description = "The role you provided is invalid."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # If the multiplier is less than 1.0, send a message saying it's invalid
        if new_multiplier < 1.0:
            embed = otter_embed(interaction.user)
            embed.title = "Invalid multiplier"
            embed.description = "The multiplier must be greater than 1.0"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            # Get the level role multiplier
            data = await LevelRoleMultplier.fetch(guild_id=real_role.guild.id, role_id=real_role.id)
        except ModelNotFound:
            # If not found, send a message saying it's not found
            embed = otter_embed(interaction.user)
            embed.title = "Role doesn't have a multiplier"
            embed.description = "This role does not have a multiplier."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Set the current multiplier to the new multiplier
        data.multiplier = new_multiplier
        # Saves it to the databse
        await data.save()
        # Make/Sends the embed saying it's completed
        embed = otter_embed(interaction.user)
        embed.title = "Level multiplier role updated"
        embed.description = f"Updated {real_role.mention} as a level multiplier role with a multiplier of {new_multiplier}."
        await interaction.response.send_message(embed=embed, ephemeral=True)
    

    @level_multiplier.sub_command()
    @commands.has_permissions(manage_guild=True)
    @leveling_enabled()
    async def list_multipliers(self, interaction: disnake.GuildCommandInteraction):
        """
        List level multiplier roles
        """
        # Creates a list to hold the roles
        roles = []
        # Gets all roles for the guild
        rolesData = await LevelRoleMultplier.get_all_by_gid(interaction.guild.id)
        # Gets the guild data
        guild_data = await LevelingGuild.fetch(guild_id=interaction.guild.id)
        # For each role in the database
        for role in rolesData:
            # If role is none, disregard
            if role is None:
                return
            # Get the role from the guild
            role = interaction.guild.get_role(role.role_id) 
            if not role:
                continue
            # Append it onto the list of multiplier roles
            roles.append(role)
        # Makes/send the multiplier roles
        embed = otter_embed(interaction.author)
        embed.title = "Level Multiplier Roles"
        embed.description = f"**Roles:** {', '.join(roles)}\n**Server Multiplier:** {guild_data.leveling_server_multiplier}"
        await interaction.response.send_message(embed=embed)

    @commands.slash_command()
    @commands.has_permissions(manage_guild=True)
    @leveling_enabled()
    async def level_roles(self, interaction: disnake.GuildCommandInteraction):
        # Another sub command group
        """
        Manage level roles
        """
        pass

    @level_roles.sub_command()
    @commands.has_permissions(manage_guild=True)
    @leveling_enabled()
    async def add_level_role(self, interaction: disnake.GuildCommandInteraction, level: int, role: disnake.Role):
        """
        Add a level role

        Parameters
        ----------
        level: level to add role at
        role: role to add
        """
        try:
            # Attempts to get the level roles
            await LevelRoles.fetch(role_id=role.id)
        except ModelNotFound:
            # If not found, then create it and make/send an embed saying it's completed
            await LevelRoles(role_id=role.id, level=level, guild_id=role.guild.id).create()
            embed = otter_embed(interaction.user)
            embed.title = "Level role added"
            embed.description = f"Added {role.mention} as a level role at level {level}."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # If exceptions not thrown, make/send an embed saying it's already added
        embed = otter_embed(interaction.user)
        embed.title = "Role already exists"
        embed.description = "This role already has a level. You can remove it with `/level_roles update (role) (new_lvl)`."
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @level_roles.sub_command()
    @commands.has_permissions(manage_guild=True)
    @leveling_enabled()
    async def remove_level_role(self, interaction: disnake.GuildCommandInteraction,
                     role: str = commands.Param(autocomp=autocomp_leveling_roles)):
        """
        Remove a level role

        Parameters
        ----------
        role: role to remove
        """
        # Gets the role ID from the autocomp
        real_role = interaction.guild.get_role(int(role.split("(id:")[1].split(")")[0]))
        # If the guild doesn't have the role, send a message saying it's invalid
        if not real_role:
            embed = otter_embed(interaction.user)
            embed.title = "Invalid role"
            embed.description = "The role you provided is invalid. (Maybe deleted?)"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            # Attempts the get the level role
            level_role = await LevelRoles.fetch(role_id=real_role.id)
        except ModelNotFound:
            # If not found, send a message saying it's not found
            embed = otter_embed(interaction.user)
            embed.title = "Role doesn't have a level"
            embed.description = "This role does not have a level."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Remove it from the database and makes/sends an embed saying it's completed
        await level_role.delete()
        embed = otter_embed(interaction.user)
        embed.title = "Level role removed"
        embed.description = f"Removed {real_role.mention} from level roles."
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @level_roles.sub_command()
    @commands.has_permissions(manage_guild=True)
    @leveling_enabled()
    async def update_level_role(self, interaction: disnake.GuildCommandInteraction,
                     role: str = commands.Param(autocomp=autocomp_leveling_roles), level: int = 1):
        """
        Update a level role

        Parameters
        ----------
        role: role to update
        level: new level
        """
        # Gets the role ID from the autocomp
        real_role = interaction.guild.get_role(int(role.split("(id:")[1].split(")")[0]))
        # If the guild doesn't have the role, send a message saying it's invalid
        if not real_role:
            embed = otter_embed(interaction.user)
            embed.title = "Invalid role"
            embed.description = "The role you provided is invalid. (Maybe deleted?)"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            # Attempts to get the role
            level_role = await LevelRoles.fetch(role_id=real_role.id)
        except ModelNotFound:
            # If not found, send a message saying it's not found
            embed = otter_embed(interaction.user)
            embed.title = "Role doesn't have a level"
            embed.description = "This role does not have a level."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Update the level and save it to the database
        level_role.level = level
        await level_role.save()
        # Make/Sends the embed saying it's completed
        embed = otter_embed(interaction.user)
        embed.title = "Level role updated"
        embed.description = f"Updated {real_role.mention} to level {level}."
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @level_roles.sub_command()
    @commands.has_permissions(manage_guild=True)
    @leveling_enabled()
    async def list_roles(self, interaction: disnake.GuildCommandInteraction):
        """
        List all level roles
        """
        # Gets all the level roles
        level_roles = await LevelRoles.get_all_by_gid(guild_id=interaction.guild.id)
        # Makes the embed and adds the level roles to the description
        embed = otter_embed(interaction.author)
        embed.title = "Level Roles"
        # If no roles are found then say there are no level roles
        if len(level_roles) == 0:
            embed.description = "No level roles"
        else:
            # For each guild in the data base then it'll add it to the description
            embed.description = "\n".join(
                [f"Level {level_role.level}: <@&{level_role.role_id}>" for level_role in level_roles])
        await interaction.response.send_message(embed=embed)

    @commands.slash_command()
    @commands.has_permissions(manage_guild=True)
    async def level(self, interaction: disnake.CommandInteraction):
        # Another sub command group
        pass

    @level.sub_command()
    @commands.has_permissions(manage_guild=True)
    async def add_levels(self, interaction: disnake.GuildCommandInteraction, user: disnake.User,
                  levels: int = 0, xp: int = 0):
        """
        Add levels and xp to a user

        Parameters
        ----------
        user: The user to add levels and xp to
        levels: The amount of levels to add
        xp: The amount of xp to add
        """
        # Checks if one and/or the other param are provided 
        if levels < 0 or xp < 0 and levels + xp <= 0:
            embed = otter_embed(interaction.author)
            embed.title = "Invalid amount"
            embed.description = "You must add at least 1+ level or 1+ xp"
            return
        # Gets the guild data
        guild_schema = await LevelingGuild.fetch(guild_id=interaction.guild.id)
        # Converts Level -> XP
        adding_levels = convertLevelToXP(levels, guild_schema.leveling_xp_base)
        # Gets the user data
        user_schema = await LevelUsers.fetch(user_id=user.id, guild_id=interaction.guild.id)
        # Adds the xp provided in the comand plus converted xp to the user
        user_schema.xp += adding_levels + xp
        # Saves it into the database
        await user_schema.save()
        # Makes/creates the embed saying it added the level and/or xp
        embed = otter_embed(interaction.author)
        embed.title = "Levels and xp added"
        embed.description = f"Added {levels} levels and {xp} xp to {user.mention}"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @level.sub_command()
    @commands.has_permissions(manage_guild=True)
    async def remove_levels(self, interaction: disnake.GuildCommandInteraction, user: disnake.User,
                     levels: int = 0, # type: ignore
                     xp: int = 0): # type: ignore
        """
        Remove levels and xp from a user

        Parameters
        ----------
        user: The user to remove levels and xp from
        levels: The amount of levels to remove
        xp: The amount of xp to remove
        """
        # Checks if one and/or the other param are provided
        if levels < 0 or xp < 0 and levels + xp <= 0:
            embed = otter_embed(interaction.author)
            embed.title = "Invalid amount"
            embed.description = "You must remove at least 1+ level and/or 1+ xp"
            return
        # Gets the guild data
        guild_schema = await LevelingGuild.fetch(guild_id=interaction.guild.id)
        # Converts Level -> XP
        removing_levels = convertLevelToXP(levels, guild_schema.leveling_xp_base)
        # Gets the user Data
        user_schema = await LevelUsers.fetch(user_id=user.id, guild_id=interaction.guild.id)
        # Removes the xp provided in the comand plus converted xp from the user
        user_schema.xp -= removing_levels + xp
        # If the XP is zero, then set them to 0 (to avoid negative xp)
        if user_schema.xp < 0:
            user_schema.xp = 0
        # Saves it into the database
        await user_schema.save()
        # Makes the embed saying it removed the level and/or xp
        embed = otter_embed(interaction.author)
        embed.title = "Levels and xp removed"
        embed.description = f"Removed {levels} levels and {xp} xp from {user.mention}"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        # Get the guild data
        guild_data = await LevelingGuild.fetch(guild_id=member.guild.id)
        # Check if leveling is enabled
        if not guild_data.leveling_enabled:
            return
        try:
            # Attempts to get the user data
            await LevelUsers.fetch(user_id=member.id, guild_id=member.guild.id)
            self.bot.log.info(f"Found user {member.id} in guild {member.guild.id} (RE-JOINING)")
        except ModelNotFound:
            # If not found, create it
            await LevelUsers(user_id=member.id, guild_id=member.guild.id).create()    
            self.bot.log.info(f"Created user {member.id} in guild {member.guild.id} (NEW USER)")      
            
        return

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if not message.guild:
            return
        if message.author.bot:
            return
        # Gets the guild data
        guild_data = await LevelingGuild.fetch(guild_id=message.guild.id)
        # If leveling is not enabled, disregard
        if not guild_data.leveling_enabled:
            return
        # If the guild doesn't have a blacklisted channel list, create one
        if guild_data.leveling_blacklisted_channel is None:
            guild_data.leveling_blacklisted_channel = []
            await guild_data.save()
        # If the channel is blacklisted, disregard
        if message.channel.id in guild_data.leveling_blacklisted_channel:
            return
        # If the user is in the temp list, disregard (The bot has to finish processing the previous message)
        if self.bot.xp_temp.count(message.author.id) > 0:
            return
        # Adds it to the temp list
        self.bot.xp_temp.append(message.author.id)
        # Gets the user Data
        user_data = await LevelUsers.fetch(user_id=message.author.id, guild_id=message.guild.id)
        # Checks if the user is in the cooldown list
        if self.bot.xp_cooldown.get(message.author.id) is None: # type: ignore
            # If not, set their number to 0
            self.bot.xp_cooldown[message.author.id] = 0 # type: ignore
        # If cooldown is greater than the max messages per min configured, disregard
        if self.bot.xp_cooldown[message.author.id] >= guild_data.leveling_earnable_messages_per_min: # type: ignore
            return
        # Generate a random number between the min and max xp per message
        new_xp = random.randint(guild_data.leveling_xp_per_message_min,
                                guild_data.leveling_xp_per_message_max)
        # Base Multiplier
        multiplier = 1.0
        # Apply multipliers
        if guild_data.leveling_server_multiplier:
            multiplier *= guild_data.leveling_server_multiplier
        # Get member data for the user
        member =  message.guild.get_member(message.author.id)
        # If the member is not found, disregard
        if member is None:
            return
        # For Each role
        for role in member.roles:
            try:
                # Get the role level data for each role they have
                level_role = await LevelRoleMultplier.fetch(role_id=role.id)
            except ModelNotFound:
                continue
            # Adds the multiplier for each guild with a multiplier
            multiplier *= level_role.multiplier
        # Multiplies the xp by the multiplier
        new_xp *= multiplier
        # Get the old level and new level
        old_level = convertXPToLevel(user_data.xp, guild_data.leveling_xp_base)
        new_level = convertXPToLevel(user_data.xp + new_xp, guild_data.leveling_xp_base)
        # If new level is greater
        if old_level < new_level:
            # Get the level role data
            level_roles = await LevelRoles.get_all_by_gid(guild_id=message.guild.id)
            # Setup data for the lowest role
            lowest_role = None
            previous_role = None
            reward = None
            # Sort the level roles by level and go through it
            for role in sorted(list(level_roles), key=lambda x: x.level):
                # If the new level is greater than or equal to the role level
                if new_level >= role.level:
                    # Set the role to the latest role
                    print(f"Highest Role so far: {role.role_id}")
                    previous_role = lowest_role
                    # Sets the previous role to role (This is to get the previous role)
                    print("Previous Role: ", previous_role)
                    # Sets the lowest role to the role
                    lowest_role = role

            if lowest_role:
                print("Lowest Role: ", lowest_role)
                # Get lowest role
                role = message.guild.get_role(lowest_role.role_id)
                # Checks if the role is found and if the member doesn't have the role
                if role and member not in role.members:
                    # Adds that role to the member
                    await member.add_roles(role)
                    reward = f"You have received {role.mention} role for reaching that level!"
            # if previous_role and previous_role.level < new_level:
            #     prev_role = message.guild.get_role(previous_role.role_id)
            #     if prev_role and message.author in prev_role.members:
            #         await member.remove_roles(prev_role)
                # Go through each level role sorted by level
                for role in sorted(list(level_roles), key=lambda x: x.level):
                    # If the role is the lowest role, disregard
                    if role.id == lowest_role.id:
                        continue
                    # Get the role from the guild
                    temp_role = message.guild.get_role(role.role_id)
                    if not temp_role:
                        continue
                    # Remove any other roles the user is not supposed to have
                    if member in temp_role.members:
                        await member.remove_roles(temp_role)
            # Make the embed for the level up message
            embed = otter_embed(message.author)
            levelup_msg = guild_data.leveling_xp_per_message_levelup_msg
            embed.title = "Level up!"
            # Sets the image to the user's avatar
            embed.set_image(message.author.display_avatar.with_size(128))
            # If the level up message is not set, make one
            if levelup_msg is None:
                levelup_msg = f"{message.author.mention} has leveled up to level {new_level}"
            else:
                # Otherwise replace the placeholders from the configured
                embed.description = levelup_msg.replace("%user", message.author.mention).replace("%level", str(new_level)).replace("%reward", reward if reward else '')
            # If the level up channel is set, send it in the channel
            if guild_data.leveling_xp_per_message_levelup_channel is not None:
                channel = message.guild.get_channel(guild_data.leveling_xp_per_message_levelup_channel)
                if isinstance(channel, disnake.TextChannel):
                    await channel.send(embed=embed)
            else:
                # Sends the embed in the channel the message was sent in
                await message.channel.send(embed=embed)
        # Adds them to the xp cooldown
        self.bot.xp_cooldown[message.author.id] += 1
        # Gets user data
        user_data = await LevelUsers.fetch(user_id=message.author.id, guild_id=message.guild.id)
        # Adds the XP
        user_data.xp += int(new_xp)
        self.bot.log.info(f"{message.author} earned {new_xp} XP")
        # Rempve it from the xp_temp (meaning it's done processing)
        self.bot.xp_temp.remove(message.author.id)
        # Saves it to the database
        await user_data.save()

        

def setup(bot: commands.Bot):
    bot.add_cog(LevelingCog(bot))