import io
import apgorm

import disnake
from disnake.ext import commands
from modules.ottermail.database.model import Modmail, ModmailGuild

from utils.embeds import otter_embed


class ModmailCog(commands.Cog):
    def __init__(self, bot: disnake.Client):
        self.bot = bot
        
    @commands.Cog.listener()
    # Displays the typing indicator when a user types in the Bot's DM with the Modmail thread open
    async def on_raw_typing(self, data: disnake.RawTypingEvent):
        # Gets the channel
        channel = self.bot.get_channel(data.channel_id)
        # Gets the user
        user = self.bot.get_user(data.user_id)
        # If neither exists, then stop
        if not user or data.guild_id:
            return
        modmail = await Modmail.find_or_fail_buid(user.id)
        if modmail:
            # Gets the Guild Data from modmail data
            guild = self.bot.get_guild(modmail.guild_id)
            # If the guild doesn't exist, then stop
            if not guild:
                return
            # Gets the channel from the guild data
            channel = guild.get_channel(modmail.modmail_channel_id)
            if isinstance(channel, disnake.TextChannel):
                # If the channel is a text channel, then trigger typing
                await channel.trigger_typing()

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return
        # Check channel types. (This will run )
        if message.channel.type == disnake.ChannelType.private:
            # Gets the modmail by user ID
            modmail = await Modmail.find_or_fail_buid(message.author.id)
            if modmail:
                # If modmail is a open-channel modmail, then don't do anything else
                if modmail.no_dm:
                    return
                # Gets the receiver and channel via modmail data
                receiver = self.bot.get_guild(modmail.guild_id)
                channel = receiver.get_channel(modmail.modmail_channel_id)
                # Handles Attachments (if any)
                if len(message.attachments) > 0:
                    images = []
                    for attachment in message.attachments:
                        fp = io.BytesIO()
                        await attachment.save(fp)
                        fp.seek(0)
                        images.append(disnake.File(fp, attachment.filename))
                    await channel.send(files=images, content=f"{message.author.mention}: {message.clean_content}")
                else:
                    # Otherwise send the message as is
                    await channel.send(f"{message.author}: {message.clean_content}")
                # React checkmark to indicate that the message was sent
                await message.add_reaction("✅")
                return
        # If it was sent from text -> DM
        elif message.channel.type == disnake.ChannelType.text:
            # Comments are ignored
            if message.content.startswith("//"):
                return
            # Commands within the modmail channel
            elif message.content.startswith("."):
                match (message.content.split(" ")[0]):
                    case ".close":
                        # Closes modmail channel and logs it
                        guild_data = await ModmailGuild.fetch(guild_id=message.guild.id)
                        modmail = await Modmail.fetch(modmail_channel_id=message.channel.id)
                        user = self.bot.get_user(modmail.user_id)
                        await modmail.close_modmail(message.guild, user, message.channel)
                        if modmail.no_dm:
                            return
                        await user.send(f"Your modmail is now closed.")
                        return
                    # Gets infomration of the modmail
                    case ".info":
                        modmail = await Modmail.find_or_fail_bcid(message.channel.id)
                        if modmail:
                            receiver = self.bot.get_user(modmail.user_id)
                            if receiver:
                                embed = otter_embed(message.author)
                                embed.title = "Modmail Info"
                                embed.description = f"User: {receiver.mention}\nModmail Channel: {message.channel.mention}"
                                await message.channel.send(embed=embed)
                            else:
                                await message.channel.send(f"Could not find user with ID {modmail['userID']}")
                            return
                return
            # Gets modmail via channel ID
            modmail = await Modmail.find_or_fail_bcid(message.channel.id)
            if modmail:
                # If modmail is open-channel. Don't do anything else
                if modmail.no_dm:
                    return
                # Get the receiver via modmail data
                receiver = self.bot.get_user(modmail.user_id)
                if receiver:
                    # Handle attachments (if any)
                    if len(message.attachments) > 0:
                        images = []
                        for attachment in message.attachments:
                            fp = io.BytesIO()
                            await attachment.save(fp)
                            fp.seek(0)
                            images.append(disnake.File(
                                fp, attachment.filename))
                        try:
                            # Send Attachments
                            await receiver.send(files=images, content=f"Staff Member: {message.clean_content}")
                        except (disnake.Forbidden, disnake.HTTPException):
                            # If not, react X to indicate that it didn't went through and the error
                            await message.add_reaction("❌")
                            await message.channel.send(f"Could not send message to user {receiver.mention}.")
                    else:
                        try:
                            # Send the message as is
                            await receiver.send(f"Staff Member: {message.clean_content}")
                        except (disnake.Forbidden, disnake.HTTPException):
                            # React X to indicate that it didn't went through and the error
                            await message.add_reaction("❌")
                            await message.channel.send(f"Could not send message to user {receiver.mention}.")
                            return
                    # If everything went through, react checkmark to indicate that the message was sent
                    await message.add_reaction("✅")
                else:
                    # If the user left/doesn't exist, then stop
                    await message.channel.send(f"Could not find user with ID {modmail['userID']}")
                    channel = message.channel.get_thread(message.channel.id)
            return

    @commands.slash_command(
        name="send_modmail_msg",
        description="Send the modmail instruction and option to begin in the specified channel.",
    )
    @commands.has_permissions(manage_guild=True)
    async def send_modmail_message(self, interaction: disnake.CommandInteraction, channel: disnake.TextChannel):
        if not channel:
            # If no channel is specified (which shouldn't happen)
            return await interaction.send("Please specify a channel. This can be a name, mention or ID")
        # Get the guild data from the guild id
        guild_data = await ModmailGuild.fetch(guild_id=interaction.guild.id)
        # If the guild data isn't configured properly, then stop and send the error
        if not guild_data.modmail_category_id or not guild_data.modmail_log_channel_id:
            return await interaction.response.send_message("Please make sure you setup a Modmail Category AND Modmail Log before using the Modmail System", ephemeral=True)
        # Generate the instruction embed with the button 
        embed = otter_embed(interaction.author)
        instructions = guild_data.modmail_instruction
        embed.title = "Modmail!"
        embed.description = instructions if instructions else "Open a modmail by pressing this button below."
        # Sends the embed to the specified channel listening 24x7 for the button
        await channel.send(embed=embed, view=ModmailButton())
        await interaction.send("Sent modmail message to channel.")
        
    @commands.slash_command(
        name="contact",
        description="Open a Modmail directly to a user"
    )
    @commands.has_permissions(view_audit_log=True)
    async def contact(self, interaction: disnake.GuildCommandInteraction, user: disnake.Member):
        """This will open a modmail directly to a user

            user: User in questioning
        """
        open = False
        # Gets the guild data
        guild_data = await ModmailGuild.fetch(guild_id=interaction.guild.id)
        # If the guild data isn't configured properly, then stop and send the error
        if not guild_data.modmail_category_id:
            return await interaction.response.send_message("Please set a modmail category (along with modmail log channel) before contacting users", ephemeral=True)

        # Checks if the user has a modmail open
        try:
            # Attempt to get the modmail data
            await Modmail.fetch(user_id=user.id)
        except apgorm.exceptions.ModelNotFound:
            # If it throws an error about not finding the error then continue
            # Get the category from the guild data
            category = interaction.guild.get_channel(guild_data.modmail_category_id)
            # If the modmail is not open then send a message to the user
            if not open:
                try:
                    await user.send(f"Hello There! A Staff member from {interaction.guild.name} is wanting to reach out to you. A Staff member will shortly ask you questions here in my DMs, you have the ability to send Attachment and Files.")
                except disnake.Forbidden:
                    await interaction.response.send_message("I was unable to send a message to the user, they DO NOT have their DMs Open. (Consider making the channel open by making open true)")
                    return
            # Create the channel (if the message went through)
            channel = await category.create_text_channel(f'staff-mm-{user.id}')
            # Send the message to the newly created channel
            await channel.send(f"{interaction.user} has created a channel between the Staff Team and {user}.\nStaff: `.close` will close and log the modmail channel.\n{'Messages starting with `//` will **NOT** be sent to the user' if open is False else ''}"
            )
            # Get the staff role and ping it
            staff_role = guild_data.modmail_staff_role_id
            role = interaction.guild.get_role(staff_role)
            if role:
                m = await channel.send(f"Staff role: {role.mention}")
                await m.delete()
                # Set staff to see it (just in case)
                await channel.set_permissions(role, view_channel=True, send_messages=True)
            if open:
                # If the modmail is open, then give access to the user to see the channel
                await channel.set_permissions(user, view_channel=True, send_messages=True, embed_links=True, attach_files=True)
                await channel.send(f"Hello There {user.mention}! The Staff team is wanting to reach out to you. A Staff member will shortly ask you questions here in this channel. You are granted permission to send files/attachments as needed.")
                await Modmail(guild_id=interaction.guild.id, user_id=user.id, modmail_channel_id=channel.id, no_dm=True).create()
                return
            # Create modmail data for the user
            await Modmail(guild_id=interaction.guild.id, user_id=user.id, modmail_channel_id=channel.id, no_dm=False).create()
            # Send the message as a response to indicate that it go through
            await interaction.response.send_message(f"Created Modmail Channel in {channel.mention}", ephemeral=True)
            return
        # If there were no errors thrown for having a modmail data for the user then throw an error
        return await interaction.response.send_message("Users cannot have more than one Modmail open", ephemeral=True)
        
    


class ModmailButton(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="Open Modmail", style=disnake.ButtonStyle.green, custom_id="modmail:open"
    )
    # When the open modmail button is pushed
    async def open_modmail(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        # Get the guild data
        guild_data = await ModmailGuild.fetch(guild_id=interaction.guild.id)
        # If the guild data isn't configured properly then error with message
        if not guild_data.modmail_category_id or not guild_data.modmail_log_channel_id:
            return await interaction.response.send_message("Please contact staff and make sure they setup a Modmail Category AND Modmail Log before using the Modmail System", ephemeral=True)
        
        try:
            # Attempt the get the modmail data
            await Modmail.fetch(user_id=interaction.user.id)
        except apgorm.exceptions.ModelNotFound:
            # If it throws an error about not finding the error then continue
            try:
                category = interaction.guild.get_channel(
                    guild_data.modmail_category_id)
                try:
                    # Sends the user 
                    await interaction.user.send("Testing", delete_after=3)
                except disnake.Forbidden:
                    return await interaction.response.send_message(
                        "I was unable to send the message to you, be sure dms are open so I can dm you!", ephemeral=True)
                # Creates a channel if the message went through
                channel = await category.create_text_channel(f"modmail-{interaction.user.id}")
                await interaction.response.send_message("I have opened a modmail! Check your dms!", ephemeral=True)
                await channel.send(
                    f"{interaction.user} ({interaction.user.id}) has opened a modmail channel!\n\nMessages starting with `//` "
                    f"will **NOT** be sent to the user.\n`.close` will close and log the modmail channel")
                # If the staff role exist, ping it
                if guild_data.modmail_staff_role_id:
                    m = await channel.send(f"Staff role: <@&{guild_data.modmail_staff_role_id}>")
                    await m.delete()
                # Sends the message to the user saying that the modmail has been created
                await interaction.user.send(
                    "Heya! You've have opened up a Modmail Channel. Please describe what are you wanting to ask/report to the "
                    "staff team for this server. Please make sure that you are elaborate with your message")
                await Modmail(guild_id=interaction.guild.id, user_id=interaction.user.id, modmail_channel_id=channel.id).create()
                return
            except () as e:
                # If any errors went through then send it
                await interaction.response.send_message("It appears the an unexpected error has occurred while opening your modmail. Please try again and if it presist contact Ozzy with the following error:\n\n{e}", ephemeral=True)
        # If there was no error regarding about having a modmail open, then send an error
        return await interaction.response.send_message("You cannot have more than one Modmail open", ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ModmailCog(bot))
