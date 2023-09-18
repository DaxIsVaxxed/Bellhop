import copy
import io
from datetime import datetime
from typing import Optional
import disnake
from disnake import Client
from disnake.ext import commands
import apgorm
from modules.otterverify.utils.embeds import otter_embed
from modules.otterverify.utils.helpers import ask_reason, get_guild_data, get_verif_delete, get_verification, text_reason
from modules.otterverify.database.model import VerificationApp, VerificationStatus, VerificationGuild


class VerificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Typing Feedback for Verification Questioning Channels
    @commands.Cog.listener()
    async def on_raw_typing(self, data: disnake.RawTypingEvent):
        # Get Channel and user (The stuff is raw)
        channel = self.bot.get_channel(data.channel_id)
        user = self.bot.get_user(data.user_id)
        # If can't find user/guild, don't bother
        if not user or data.guild_id:
            return
        # Private channel
        try:
            # Get verification application
            verification = await VerificationApp.fetch(user_id=user.id, questioning=True)
        except apgorm.exceptions.ModelNotFound:
            # If not found, don't bother
            return
        guild = self.bot.get_guild(verification.guild_id)
        # If you can find guild, or the questioning channel, don't bother
        if not guild:
            return
        if verification.questioning_channel_id is None:
            return
        # Get channel
        channel = guild.get_channel(verification.questioning_channel_id)
        # If the channel is found and is a text channel, trigger the typing
        if channel and isinstance(channel, disnake.TextChannel):
            await channel.trigger_typing()


    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        guild = member.guild
        # Fetch the audit log to check for kick or ban events
        async for entry in guild.audit_logs(limit=5, action=disnake.AuditLogAction.kick):
            if entry.target.id == member.id:
                return

        async for entry in guild.audit_logs(limit=5, action=disnake.AuditLogAction.ban):
            if entry.target.id == member.id:
                return
        # Gather Data from the Database
        guild_data = await get_guild_data(member.guild.id)
        verification = await VerificationApp.find_or_fail(user_id=member.id, guild_id=member.guild.id)
        if not verification:
            return
        if guild_data.pending_verifications_channel_id is None:
            # TODO: Add Bot Alert
            print("Pending Verifications Channel ID is None. Please set it up.")
            return
        # Get's the Pending Channel ID
        channel = member.guild.get_channel(
            guild_data.pending_verifications_channel_id)
        if channel is None or not isinstance(channel, disnake.TextChannel):
            # TODO: Add Bot Alert
            print(
                "Pending Verifications Channel ID is not a text channel. Please set it up.")
            return
        msg = await channel.fetch_message(verification.pending_verification_id)
        # if verification.questioning and verification.questioning_channel_id:
        #     questioning_channel = member.guild.get_channel(
        #         verification.questioning_channel_id)
        #     if questioning_channel is None or not isinstance(questioning_channel, disnake.TextChannel):
        #         # TODO: Add Bot Alert
        #         print("Questioning Channel ID is not a text channel or non-existent.")
        #         return
        #     await questioning_channel.send("User has left the server.")
        #     await questioning_channel.delete()
        await verification.close_verification(self.bot.user, self.bot, member.guild, VerificationStatus.LEFT, message=msg)

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return
        ################## USER DMS ###################
        if isinstance(message.channel, disnake.DMChannel):
            verification_data = await get_verification(message.author.id)
            # Check if the user is being questioned.
            if verification_data is not None and verification_data.questioning:
                receiver = self.bot.get_guild(verification_data.guild_id)
                if not receiver:
                    print("Guild not found. Is it deleted???")
                    await message.add_reaction("❌")
                    return
                if verification_data.questioning_channel_id is None:
                    return
                channel = receiver.get_channel(
                    verification_data.questioning_channel_id)
                if channel is None or not isinstance(channel, disnake.TextChannel):
                    print(
                        "Questioning Channel ID is not a text channel or non-existent.")
                    return
                # Handles Attachments
                if len(message.attachments) > 0:
                    images = []
                    for attachment in message.attachments:
                        fp = io.BytesIO()
                        await attachment.save(fp)
                        fp.seek(0)
                        images.append(disnake.File(fp, attachment.filename))
                    try:
                        await channel.send(files=images, content=f"{message.author.mention}: {message.clean_content}")
                    except Exception as e:
                        await message.channel.send(
                            f"An Error Occured while sending that message. Please try again later.\n\nError: {e}")
                        await message.add_reaction("❌")
                        return
                else:
                    # Handles normal messages
                    try:
                        await channel.send(f"{message.author.mention}: {message.clean_content}")
                    except Exception as e:
                        await message.channel.send(
                            f"An Error Occured while sending that message. Please try again later.\n\nError: {e}")
                        await message.add_reaction("❌")
                        return
                await message.add_reaction("✅")
            return
        elif isinstance(message.channel, disnake.TextChannel) and message.guild:
            try:
                verification_data = await VerificationApp.fetch(guild_id=message.guild.id,
                                                                questioning_channel_id=message.channel.id)
                guild_data = await VerificationGuild.fetch(guild_id=message.guild.id)
            except apgorm.exceptions.ModelNotFound:
                return
            if not guild_data.pending_verifications_channel_id:
                print("There's not a a pending verification channel set")
                await message.add_reaction("❌")
                return
            if message.content.startswith("//"):
                return
            elif message.content.startswith("!!"):
                match (message.content.split(" ")[0]):
                    # Questioning Channels Command
                    case "!!accept":
                        await accept_user(self.bot, guild_data, message)
                        return
                    case "!!deny":
                        await deny_user(self.bot, message)
                        return
                    case "!!kick":
                        await kick_user(self.bot, message)
                        return
                    case "!!ban":
                        await ban_user(self.bot, message)
                        return
            else:
                verification = await VerificationApp.find_or_fail_bqid(channel_id=message.channel.id)
                if verification is not False and verification.questioning:
                    receiver = self.bot.get_user(verification.user_id)
                    if receiver:
                        if len(message.attachments) > 0:
                            images = []
                            for attachment in message.attachments:
                                fp = io.BytesIO()
                                await attachment.save(fp)
                                fp.seek(0)
                                images.append(disnake.File(
                                    fp, attachment.filename))
                            await receiver.send(files=images, content=f"Staff Member: {message.clean_content}")
                        else:
                            await receiver.send(f"Staff Member: {message.clean_content}")
                        await message.add_reaction("✅")
                    else:
                        await message.channel.send(f"Could not find user with ID {verification.user_id}")
                        channel = message.channel.get_thread(
                            message.channel.id)
                return

    @commands.slash_command(
        name="check",
        description="Checks if the guild is all set"
    )
    @commands.has_permissions(manage_guild=True)
    async def check(self, interaction: disnake.GuildCommandInteraction):
        # Guild Guild Data
        verification_guild = await VerificationGuild.fetch(guild_id=interaction.guild.id)

        # Check if all required fields are set up
        is_set_up = all([
            verification_guild.verification_logging_channel,
            verification_guild.verification_questions,
            verification_guild.unverified_role_ids,
            verification_guild.verified_role_ids,
            verification_guild.verification_instructions,
            verification_guild.pending_verifications_channel_id,
            verification_guild.welcome_role_id,
            verification_guild.welcome_channel_id,
            verification_guild.welcome_message,
            verification_guild.joining_message,
            verification_guild.staff_role_id,
        ])

        # Create an embed to display the result
        embed = Embed(
            title="Verification Guild Check",
            description=f"Verification Guild setup status: {'✅ Complete' if is_set_up else '❌ Incomplete'}",
            color=disnake.Color.green() if is_set_up else disnake.Color.red(),
        )

        if not is_set_up:
            embed.add_field(name="Next Steps",
                            value="Please configure all required fields in the VerificationGuild model to complete the setup.")

        # Send the embed
        await interaction.response.send_message(embed=embed)

    @commands.slash_command(
        name="send_verify_msg",
        description="Send the verification instruction and option to begin in the specified channel.",
    )
    @commands.has_permissions(manage_guild=True)
    async def send_verify_message(self, interaction: disnake.GuildCommandInteraction, channel: disnake.TextChannel):
        # Get verification data
        guild_data = await VerificationGuild.fetch(guild_id=interaction.guild.id)
        # If there's no questions then error
        if len(guild_data.verification_questions) == 0:
            await interaction.response.send_message(
                "You cannot send the Verification Button if there's no questions set!")
        embed = otter_embed(interaction.user)
        # Makes and send verification data
        verify_message = guild_data.verification_instructions
        embed.title = "Welcome to the Server!"
        embed.description = verify_message if verify_message else "Please verify yourself by clicking the button below."
        await channel.send(embed=embed, view=VerifyButton())
        await interaction.response.send_message("Verification message sent!", ephemeral=True)


class ContinueButton(disnake.ui.View):
    def __init__(self, modal_sections, current_section):
        super().__init__(timeout=None)
        self.modalSections = modal_sections
        self.currentSection = current_section

    @disnake.ui.button(
        label="Continue", style=disnake.ButtonStyle.green, custom_id="verification:continue"
    )
    async def continue_verification(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        # Get the user's verification application
        verification_data = await VerificationApp.find_or_fail(user_id=interaction.user.id,
                                                               guild_id=interaction.guild.id)
        # If the verification for that user has been made, error
        if verification_data:
            return await interaction.response.send_message("You already have an open verification!", ephemeral=True)
        await interaction.response.send_modal(
            modal=QuestionModal(self.modalSections, self.currentSection, interaction))


class QuestionModal(disnake.ui.Modal):
    user_responses = {}

    def __init__(
            self,
            modal_section: [],
            part,
            button_interaction: disnake.Interaction,
    ) -> None:
        super().__init__(title="Verification",
                         custom_id=f"verification:{part}", components=modal_section[part - 1])
        self.modal_section = modal_section
        self.part = part
        self.button_interaction = button_interaction

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        # If the user's ID doesn't match the responses listed, it'll make a new one (Tackling the another user's response is in another user's response)
        if interaction.user.id not in self.user_responses or self.part == 1:
            self.user_responses[interaction.user.id] = []
        # Get Verificztion Guild Data
        guild_data = await VerificationGuild.fetch(guild_id=interaction.guild.id)
        # Get's the questions from the guild data
        questions = guild_data.verification_questions
        # Makes a list of responses based on the responses on the model
        temp_responses = list(interaction.text_values.values())
        # For each temp response (getting the index, and response)
        for idx, response in enumerate(temp_responses):
            # Get the question based on index adding what part they're in times 5 (parts is like pages)
            question = questions[idx + ((self.part - 1) * 5)]
            # Update the user's response with the question and response
            self.user_responses[interaction.user.id].append(
                {"question": question, "response": response})
        # If there are no more questions, then submit the application
        if self.part >= len(self.modal_section):
            await self.submit_application(interaction, guild_data)
        else:
            # Other wise go back to call continue_verification which repeats this process until there are no more parts
            await self.continue_verification(interaction)

    async def submit_application(self, interaction: disnake.ModalInteraction, guild_data: VerificationGuild):
        responses = self.user_responses[interaction.user.id]
        # If there are no pending channels, then error
        if not guild_data.pending_verifications_channel_id:
            await interaction.response.send_message(
                "Staff need to set a channel for pending verification applications. Please contact staff",
                ephemeral=True
            )
            return
        channel = interaction.guild.get_channel(
            guild_data.pending_verifications_channel_id)
        user = interaction.bot.get_user(interaction.user.id)
        # Creates the base verification emebd
        embed = otter_embed(user)
        embed.title = "Avatar Reverse Search"
        embed.url = f"https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIHMP&q=imgurl:{user.display_avatar.url}"
        embed.description = "Please review this application and react with the appropriate button!"
        embed.color = disnake.Color.yellow()
        embed.set_footer(text=f"Applicant ID: {interaction.user.id}")
        embed.timestamp = datetime.utcnow()
        self.thumbnail = embed.set_thumbnail(user.display_avatar)
        member = interaction.guild.get_member(interaction.user.id)
        for i in range(len(responses)):
            embed.add_field(
                name=responses[i]['question'], value=responses[i]['response'], inline=False)
        embed.add_field(
            "Time Joined", f"<t:{int(member.joined_at.timestamp())}:R>", inline=False)
        embed.add_field(
            "Account Created", f"<t:{int(member.created_at.timestamp())}:R>", inline=False)
        try:
            # Get Verification Application if it already exist then stop the process. (Avoid Application Dupes)
            await VerificationApp.fetch(user_id=interaction.user.id, guild_id=interaction.guild.id)
            return
        except apgorm.exceptions.ModelNotFound:
            # If verification applications are not found then send the embed
            msg = await channel.send(embed=embed, content=f"<@{interaction.user.id}> {interaction.user.id}",
                                     view=ActionButton())
            await interaction.response.send_message(
                "Your application has been submitted. Please wait for staff to review your application.",
                ephemeral=True
            )
            # Create the verification application and puts it in the database
            await VerificationApp(user_id=interaction.user.id, guild_id=interaction.guild.id,
                                  pending_verification_id=msg.id).create()

    async def continue_verification(self, interaction: disnake.Interaction):
        # Sends a message to the user that they need to answer more questions and recreates the model
        await interaction.response.send_message(
            "There are more questions to answer, please continue the verification process by pressing the button below!",
            ephemeral=True,
            view=ContinueButton(self.modal_section, self.part + 1))

    async def on_error(self, error: Exception, interaction: disnake.ModalInteraction) -> None:
        # If something happens, then print the error and send the message
        print(error)
        await interaction.response.send_message(f"Oops, something went wrong.\n\nError: {error}", ephemeral=True)
        # await interaction.client.get_user(970570457269018685).send(f"Error: {error} while verifying {interaction.user}")


class VerifyButton(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="Verify", style=disnake.ButtonStyle.green, custom_id="verification:verify"
    )
    async def verify(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        # When the verification button is pushed, get the verification app and check if one already exist
        checker = await VerificationApp.find_or_fail(interaction.user.id, interaction.guild.id)
        guild_data = await VerificationGuild.fetch(guild_id=interaction.guild.id)
        # If no questions are set then error
        if len(guild_data.verification_questions) == 0:
            await interaction.response.send_message(
                "There's no questions to ask for the verification. Please inform an Staff Member to configure this bot.")
        if checker is not False:
            # If one does then send the error
            await interaction.response.send_message("You have a verification already open", ephemeral=True)
            return
        # Gets questuons
        questions = guild_data.verification_questions
        # Prepares responses, section and modal sections
        responses = []
        sections = []
        modal_sections = []
        # Have 5 questions per section
        for i in range(0, len(questions), 5):
            section = []
            for question in questions[i: i + 5]:
                section.append(question)
            sections.append(section)
        for section in sections:
            modal_components = []
            for question in section:
                # Creates the modal based on the questions set in the database
                modal_components.append(disnake.ui.TextInput(
                    label=question,
                    placeholder="Please enter your answer",
                    custom_id=f"verification:{sections.index(section)}:{section.index(question)}",
                    style=disnake.TextInputStyle.paragraph,
                    min_length=1,
                    max_length=512
                ))
            # Add it onto the modal section array
            modal_sections.append(modal_components)
        # Sends the first part (first modal)
        await interaction.response.send_modal(modal=QuestionModal(modal_sections, 1, interaction))


class Cancel(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="Cancel", style=disnake.ButtonStyle.red, custom_id="verification:cancel"
    )
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        # Cancel the verification process
        await interaction.message.edit(view=ActionButton())
        await interaction.response.send_message("Cancelled Request.", ephemeral=True)

class QuestioningButtons(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="Questioning - In Progress",
        style=disnake.ButtonStyle.gray,
        custom_id="verification:fix"
    )
    async def questioning(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        # Gets verification application
        verification_data = await VerificationApp.fetch(pending_verification_id=interaction.message.id)
        guild_data = await get_guild_data(interaction.guild.id)
        # Presets fixed to false
        fixed = False
        # Gets staff role
        staff_role = interaction.guild.get_role(guild_data.staff_role_id)
        # If user is not being questioned, disregard
        if not verification_data.questioning:
            return
        # If the user is being questioned, get channel
        channel = interaction.guild.get_channel(verification_data.questioning_channel_id)
        staff_permissions = channel.permissions_for(staff_role)
        # Check if the staff has access to the channel and fix it (if needed) (Fixing Owner-only see channel)
        if not staff_permissions.view_channel:
            await channel.set_permissions(staff_role, view_channel=True)
            fixed = True
        # Provides the message of the link and whether if it was fixed or not
        await interaction.response.send_message(f"Channel Link: {channel.jump_url}{' (Fixed Channel)' if fixed else ''}", ephemeral=True)

class ActionButton(disnake.ui.View):
    def __init__(self, disable_question=False):
        self.disable_question = disable_question
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="Accept", style=disnake.ButtonStyle.green, custom_id="verification:accept"
    )
    async def accept(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        # Gets verification guild data
        guild_data = await VerificationGuild.fetch(guild_id=interaction.guild.id)
        # Delete Duplicated Apps
        verification_data = await get_verif_delete(interaction)
        # If verificationdata is not found disregard
        if verification_data is False:
            return
        # Get user from the verification
        user = interaction.guild.get_member(verification_data.user_id)
        # Check if the user left
        if await VerificationApp.check_user_left(interaction.message, interaction.bot, user) is True:
            return

        # Get Verified, Unverified roles. Remove Unverified role(s) and add verified role(s)
        for role in guild_data.verified_role_ids:
            await user.add_roles(interaction.guild.get_role(role))
        for role in guild_data.unverified_role_ids:
            await user.remove_roles(interaction.guild.get_role(role))

        # Closes the verification
        await VerificationApp.close_verification(interaction.user, interaction.client, interaction.guild,
                                                 VerificationStatus.ACCEPTED,
                                                 interaction.message)
        # Tries to send a message to the user otherwise disregard without stopping the function
        try:
            await user.send(f"Your application has been accepted! Come and Join the Fun!")
        except (disnake.Forbidden, disnake.HTTPException):
            pass
        # Gets the welcome channel
        welcome_channel = interaction.guild.get_channel(
            guild_data.welcome_channel_id)
        embed = otter_embed(user)
        role = None
        try:
            role = interaction.guild.get_role(guild_data.welcome_role_id)
        except:
            pass
        # Forges the welcome message based on the guild data
        welcome_message = guild_data.welcome_message.replace('%member', str(interaction.guild.member_count)).replace(
            '%guild', f'{interaction.guild.name}').replace('%user', user.mention)
        if guild_data.welcome_message_banner_url:
            # Adds the banner (if set)
            embed.set_image(url=guild_data.welcome_message_banner_url)
        # Sets it as the description for the embed
        embed.description = welcome_message
        # Sends it and pinging the welcome role and user
        await welcome_channel.send(f"{role.mention if role else ''}\nWelcome {user.mention} to the server",
                                   embed=embed)
        await interaction.response.send_message("Application accepted!", ephemeral=True)

    @disnake.ui.button(
        label="Deny", style=disnake.ButtonStyle.red, custom_id="verification:deny"
    )
    async def deny(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        # Replaces the buttons with Cancel button
        await interaction.message.edit(view=Cancel())
        # Get verification applciation
        verification_data = await VerificationApp.fetch(pending_verification_id=interaction.message.id)
        # If application doesn't exist, disreagard
        if verification_data is False:
            return
        # Ask the reason
        try:
            modal_inter = await ask_reason(interaction, button)
        except:
            pass
        reason = modal_inter.text_values["reason"]
        if reason is None:
            return
        # Get user from verification data
        user = interaction.guild.get_member(verification_data.user_id)
        if await VerificationApp.check_user_left(interaction.message, interaction.bot, user) is True:
            return
        noticed = False
        # Tries to send the user their denied message otherwise disgard
        try:
            await user.send(
                f"Your application has been denied! You're given an opportunity to resubmit your application. "
                f"(Reason: {reason})")
            noticed = True
        except:
            pass
        # Close verification
        await VerificationApp.close_verification(interaction.user, interaction.client, interaction.guild,
                                                 VerificationStatus.DENIED,
                                                 interaction.message,
                                                 reason=reason, notified=noticed)

    @disnake.ui.button(
        label="Kick", style=disnake.ButtonStyle.red, custom_id="verification:kick"
    )
    async def kick(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.message.edit(view=Cancel())
        verification_data = await get_verif_delete(interaction)
        if verification_data is False:
            return
        # Ask the reason
        try:
            modal_inter = await ask_reason(interaction, button)
        except:
            pass
        try:
            reason = modal_inter.text_values["reason"]
        except:
            return
        if reason is None:
            return
        user = interaction.guild.get_member(verification_data.user_id)
        if await VerificationApp.check_user_left(interaction.message, interaction.bot, user) is True:
            return
        try:
            await user.send(
                f"You've been kicked from the server! (Reason: {reason})")
        except (disnake.Forbidden, disnake.HTTPException):
            pass

        await verification_data.close_verification(interaction.user, interaction.client, interaction.guild,
                                                   VerificationStatus.KICKED,
                                                   interaction.message,
                                                   reason=reason)
        await user.kick(reason=reason)

    @disnake.ui.button(
        label="Ban", style=disnake.ButtonStyle.red, custom_id="verification:ban"
    )
    async def banned(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.message.edit(view=Cancel())
        verification = await get_verif_delete(interaction)
        if verification is False:
            return
        # Ask the reason
        try:
            modal_inter = await ask_reason(interaction, button)
        except:
            pass
        reason = modal_inter.text_values["reason"]
        if reason is None:
            return
        
        user = interaction.guild.get_member(verification.user_id)
        if await VerificationApp.check_user_left(interaction.message, interaction.bot, user) is True:
            return
        try:
            await user.send(
                f"You've been banned from the server! (Reason: {reason})")
        except (disnake.Forbidden, disnake.HTTPException):
            pass
        await VerificationApp.close_verification(interaction.user, interaction.client, interaction.guild,
                                                 VerificationStatus.BANNED,
                                                 interaction.message,
                                                 reason=reason)
        await user.ban(reason=reason)

    @disnake.ui.button(
        label="Question", style=disnake.ButtonStyle.gray, custom_id="verification:question",
    )
    async def question(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        verification_data = await get_verif_delete(interaction)
        if verification_data is None:
            return
        if self.disable_question:
            await interaction.response.send_message(
                "An attempt to question the user recently failed please use another option.", ephemeral=True)
            return
        await interaction.message.edit(view=None)
        await interaction.response.defer()
        guild_data = await VerificationGuild.fetch(guild_id=interaction.guild.id)
        if not verification_data.questioning:
            user = interaction.guild.get_member(verification_data.user_id)
            if await VerificationApp.check_user_left(interaction.message, interaction.bot, user) is True:
                return
            try:
                await user.send(
                    "Heya, currently the staff would like to ask you a couple of questions regarding your verification. "
                    "The questioning will be taken here in your dms and you can reply to what their say by sending a "
                    "message here. Any Attachments/Images will be sent to the staff")
            except (disnake.Forbidden, disnake.HTTPException):
                embed = interaction.message.embeds[0].add_field("NOTICE",
                                                                f"{interaction.user} has attempted to question this "
                                                                f"user but failed due to most likley dms blocked ("
                                                                f"Therefore the button is disabled)",
                                                                inline=True)
                await interaction.response.send_message(
                    "Unable to question user! Reverting buttons disabling question button...", ephemeral=True)
                await interaction.message.edit(embed=embed, view=ActionButton(disable_question=True))
                return
            channel = await interaction.message.channel.category.create_text_channel(name=f"{user.name}-questioning")
            
            await channel.edit(topic=interaction.message.id)
            staff_role = interaction.guild.get_role(guild_data.staff_role_id)
            await channel.set_permissions(interaction.guild.default_role, view_channel=False, send_messages=True)
            await channel.set_permissions(staff_role, view_channel=True)
            embed = copy.deepcopy(interaction.message.embeds[0])
            embed.description = f"{interaction.user} has opened a questioning channel. All Attachments/Images will be " \
                                f"sent to the user \nCommands:\n`!!accept` - Accept the user's verification\n`!!deny " \
                                f"<REASON GOES HERE>` - Deny the user's verification\n`!!kick <REASON GOES HERE>` - " \
                                f"Deny and Kick the User\n`!!ban <REASON GOES HERE>` - Deny and Ban the User\nMessages " \
                                f"starting with `//` will NOT be sent to the user\n================================" \
                                f"============="
            await channel.send(embed=embed)
            verification_data.questioning = True
            verification_data.questioning_channel_id = channel.id
            await verification_data.save()
            await interaction.message.edit(embed=interaction.message.embeds[0],
                                           view=QuestioningButtons())
        else:
            channel = interaction.guild.get_channel_or_thread(
                verification_data.questioning_channel_id)
            await interaction.response.send_message(f"Someone is already questioning this user. Refer to {channel}",
                                                    ephemeral=True)

    @disnake.ui.button(
        label="User ID", style=disnake.ButtonStyle.gray, custom_id="verification:userid"
    )
    async def user_id(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        verification_data = await get_verif_delete(interaction)
        if verification_data is None:
            return
        await interaction.response.send_message(verification_data.user_id, ephemeral=True)
        return


def setup(bot: commands.Bot):
    bot.add_cog(VerificationCog(bot))


async def accept_user(bot: Client, guild_data: VerificationGuild, message: disnake.Message):
    if not message.guild:
        return
    verification_data = await VerificationApp.fetch(questioning_channel_id=message.channel.id)
    user = message.guild.get_member(verification_data.user_id)
    if await VerificationApp.check_user_left(message, bot, user) is True or not user:
        return
    for role in guild_data.verified_role_ids:
        if role:
            role_adding = message.guild.get_role(role)
            if role_adding:
                await user.add_roles(role_adding)
    for role in guild_data.unverified_role_ids:
        if role:
            role_removing = message.guild.get_role(role)
            if role_removing:
                await user.remove_roles(role_removing)
    notified = True
    try:
        await user.send(f"Your application has been accepted! Come and Join the Fun!")
    except:
        notified = False
    await VerificationApp.close_verification(message.author, bot, message.guild, VerificationStatus.ACCEPTED,
                                             channel_id=message.channel.id, notified=notified)
    if not guild_data.welcome_channel_id:
        # There's no Welcome Channel, therefore we can stop from there.
        return

    welcome_channel = message.guild.get_channel(guild_data.welcome_channel_id)
    if not isinstance(welcome_channel, disnake.TextChannel):
        print("Welcome channel is not a text channel")
        return

    embed = otter_embed(user)
    role = None
    try:
        role = message.guild.get_role(guild_data.welcome_role_id)
    except:
        pass
    if not guild_data.welcome_message:
        return
    welcome_message = guild_data.welcome_message.replace('%member',
                                                         str(message.guild.member_count)).replace(
        '%guild', f'{message.guild.name}').replace('%user', user.mention)
    embed.description = welcome_message
    if guild_data.welcome_message_banner_url:
            embed.set_image(url=guild_data.welcome_message_banner_url)
    await welcome_channel.send(
        f"{role.mention if role else ''}\nWelcome {user.mention} to the server", embed=embed)
    await message.channel.send("Application accepted!")
    return


async def deny_user(bot: Client, message: disnake.Message):
    ensured = await ensure_application(bot, message)
    if not ensured.success or not ensured.guild or not isinstance(ensured.channel,
                                                                  disnake.TextChannel) or not ensured.user or not ensured.reason:
        await message.channel.send(f"Something went wrong! (Error: {ensured.failure_reason})")
        return
    notified = True
    try:
        await ensured.user.send(
            f"Your application has been denied! You may redo your verification! (Reason:{ensured.reason})")
    except:
        notified = False
        pass
    await ensured.channel.send("Application denied!")
    await VerificationApp.close_verification(message.author, bot, ensured.guild, VerificationStatus.DENIED,
                                             channel_id=message.channel.id, reason=ensured.reason, notified=notified)


async def kick_user(bot: Client, message: disnake.Message):
    ensured = await ensure_application(bot, message)
    if not ensured.success or not ensured.guild or not isinstance(ensured.channel,
                                                                  disnake.TextChannel) or not ensured.user or not ensured.reason:
        await message.channel.send(f"Something went wrong! (Error: {ensured.failure_reason})")
        return
    notified = True
    # TODO: Add checker in 1.2
    try:
        await ensured.user.send(f"Your application has been denied and you've been kicked! (Reason: {ensured.reason})")
        notified = False
    except:
        pass
    try:
        await ensured.user.kick(reason=f"Kicked from verification. {ensured.reason}")
    except () as e:
        await message.channel.send(f"Something went wrong with kicking the user! {e}")
    await VerificationApp.close_verification(message.author, bot, ensured.guild, VerificationStatus.KICKED,
                                             channel_id=message.channel.id, reason=ensured.reason)


async def ban_user(bot: Client, message: disnake.Message):
    ensured = await ensure_application(bot, message, ban=True)
    if not ensured.success or not ensured.guild or not isinstance(ensured.channel,
                                                                  disnake.TextChannel) or not ensured.user or not ensured.reason:
        await message.channel.send(f"Something went wrong! (Error: {ensured.failure_reason})")
        return
    notified = True
    # TODO: Add checkers in 1.2
    try:
        await ensured.user.send(f"Your application has been denied and you've been banned! (Reason: {ensured.reason})")
    except:
        notified = False
        pass
    try:
        await ensured.user.ban(reason=f"Banned from verification. {ensured.reason}")
    except:
        await message.channel.send(f"Something went wrong with kicking the user! {e}")

    await ensured.channel.send("Application denied and user banned!")
    await VerificationApp.close_verification(message.author, bot, ensured.guild, VerificationStatus.BANNED,
                                             channel_id=message.channel.id, reason=ensured.reason)


class ApplicationResult:
    def __init__(
            self,
            success: bool,
            failure_reason: Optional[str] = None,
            reason: Optional[str] = None,
            guild: Optional[disnake.Guild] = None,
            user: Optional[disnake.Member] = None,
            channel: Optional[disnake.TextChannel] = None,
    ):
        self.success = success
        self.failure_reason = failure_reason
        self.reason = reason
        self.guild = guild
        self.user = user
        self.channel = channel


async def ensure_application(
        bot: disnake.Client, message: disnake.Message, ban=False
) -> ApplicationResult:
    try:
        if not ban:
            reason = await text_reason(message, message.content[6:])
        else:
            reason = await text_reason(message, message.content[5:])
        if not isinstance(reason, str) or not message.guild or not isinstance(
                message.channel, disnake.TextChannel
        ):
            return ApplicationResult(success=False, failure_reason="Invalid reason")

        verification_data = await VerificationApp.find_or_fail_bqid(message.channel.id)
        if not verification_data:
            return ApplicationResult(success=False, failure_reason="No verification data")
        user = message.guild.get_member(verification_data.user_id)

        if await VerificationApp.check_user_left(message, bot, user) or not user:
            return ApplicationResult(success=False, failure_reason="User left")

        return ApplicationResult(
            success=True,
            reason=reason,
            guild=message.guild,
            user=user,
            channel=message.channel,
        )

    except Exception as e:
        return ApplicationResult(success=False, failure_reason=str(e))
