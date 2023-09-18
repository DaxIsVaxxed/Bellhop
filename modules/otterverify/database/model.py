from enum import Enum
import io
from typing import Optional
import apgorm

import apgorm as orm
import disnake
from apgorm.types import BigInt, Boolean, Array, Text, Serial


class VerificationGuild(orm.Model):
    guild_id = BigInt().field()
    # Verification Configuration
    verification_logging_channel = BigInt().nullablefield(default=None)
    verification_questions = Array(Text()).field(default=[])
    unverified_role_ids = Array(BigInt()).field(default=[])
    verified_role_ids = Array(BigInt()).field(default=[])
    verification_instructions = Text().nullablefield(default=None)
    pending_verifications_channel_id = BigInt().nullablefield(default=None)

    # Welcome Configuration
    welcome_role_id = BigInt().nullablefield(default=None)
    welcome_channel_id = BigInt().nullablefield(default=None)
    welcome_message = Text().nullablefield(default=None)
    joining_message = Text().nullablefield(default=None)
    welcome_message_banner_url = Text().nullablefield(default=None)

    staff_role_id = BigInt().nullablefield(default=None)

    primary_key = (guild_id,)


class VerificationStatus(Enum):
    ACCEPTED = 'accepted'
    DENIED = 'denied'
    BANNED = 'banned'
    KICKED = 'kicked'
    LEFT = 'left'


class VerificationApp(orm.Model):
    id = Serial().field()
    # Way to identify the verification application
    user_id = BigInt().field()
    guild_id = BigInt().field()
    pending_verification_id = BigInt().field()
    # Verification Status
    questioning = Boolean().field(default=False)
    questioning_channel_id = BigInt().nullablefield(default=None)

    primary_key = (id,)

    @staticmethod
    async def find_or_fail(user_id: int, guild_id: int):
        try:
            verification = await VerificationApp.fetch(user_id=user_id, guild_id=guild_id)
        except apgorm.exceptions.ModelNotFound:
            return False
        return verification

    @staticmethod
    async def find_or_fail_bqid(channel_id: int):
        try:
            verification = await VerificationApp.fetch(questioning_channel_id=channel_id)
        except apgorm.exceptions.ModelNotFound:
            return False
        return verification

    @staticmethod
    async def check_user_left(message: disnake.Message, bot: disnake.Client, user: Optional[disnake.Member]):
        if message.guild is None:
            # Throw error
            raise ValueError("Message is not from a guild!")
        if not user:
            await VerificationApp.close_verification(message.author, bot, message.guild, VerificationStatus.LEFT,
                                                     message)
            return True
        return False

    @staticmethod
    async def close_verification(responder: disnake.User | disnake.ClientUser | disnake.Member, bot: disnake.Client,
                                 guild: disnake.Guild, status: VerificationStatus,
                                 message: Optional[disnake.Message] = None,
                                 channel_id: Optional[int] = None,
                                 reason: str = "No Reason Provided.", notified: bool = False):
        bot.log.info("Closing Application...")
        if message:
            bot.log.info("Message FOund")
            # If the Close Verification is coming from a message via the button/interaction
            verification = await VerificationApp.fetch(pending_verification_id=message.id)
        elif channel_id:
            bot.log.info("Channel Found instead")
            # If the Close Verification is coming from a channel via the questioning channel
            verification = await VerificationApp.fetch(questioning_channel_id=channel_id)
        else:
            bot.log.info("No Message/Channel ID Provided")
            return
        # Get Guild Data
        bot.log.info("Getting Guild Data")
        guild_data = await VerificationGuild.fetch(guild_id=guild.id)
        bot.log.info("Getting Guild Data")
        # Get the pending verification channel
        if guild_data.pending_verifications_channel_id is None:
            bot.log.info("There is no verification channel ID...")
            return
        pending_channel = guild.get_channel(
            guild_data.pending_verifications_channel_id)
        if message is None:
            if not isinstance(pending_channel, disnake.TextChannel):
                bot.log.info("Pending Verification Channel is not set up. Skipping...")
                
                return
            message = await pending_channel.fetch_message(verification.pending_verification_id)

        message.embeds[0].description = "This verification has been closed by a staff member."
        message.embeds[0].add_field("Status", f"**{status.name}**")
        message.embeds[0].add_field("Responsible:", f"{responder.mention}")

        # Based on the status, modify the embed
        match status:
            case VerificationStatus.ACCEPTED:
                message.embeds[0].color = 0x00ff00
            case VerificationStatus.DENIED:
                message.embeds[0].color = 0xff0000
                message.embeds[0].add_field("Reason", reason, inline=True)
                message.embeds[0].add_field("Notified:",
                                            f"{'User was never notified (Blocked DMs)' if not notified else 'User is notified.'}",
                                            inline=False)
            case VerificationStatus.BANNED:
                message.embeds[0].color = 0xffff00
                message.embeds[0].add_field("Reason", reason, inline=False)
                message.embeds[0].add_field("Notified:",
                                            f"{'User was never notified (Blocked DMs)' if not notified else 'User is notified.'}",
                                            inline=False)
            case VerificationStatus.KICKED:
                message.embeds[0].color = 0x00ffff
                message.embeds[0].add_field("Reason", reason, inline=False)
                message.embeds[0].add_field("Notified:",
                                            f"{'User was never notified (Blocked DMs)' if not notified else 'User is notified.'}",
                                            inline=False)
            case VerificationStatus.LEFT:
                message.embeds[0].color = 0x00ffff

        # If logging channel not found
        if guild_data.verification_logging_channel is None:
            bot.log.info("Logging Channel Not setup")
            return
        # Get logging channel
        logging_channel = guild.get_channel(
            guild_data.verification_logging_channel)
        # If logging channel is not a text-based channel
        if not isinstance(logging_channel, disnake.TextChannel):
            bot.log.info("Logging channel is not a text channel")
            return
        # Delete Verification
        await message.delete()
        # If Verification System is used... otherwise skip questioning closing parts
        if verification.questioning:
            # If guild is not a guild or there's no questioning channel cancel process.
            if not isinstance(message.guild, disnake.Guild) or not verification.questioning_channel_id:
                bot.log.info("Cannot find questioning channel...")    
                return
            # Get questioning channel
            questioning_channel = message.guild.get_channel(
                verification.questioning_channel_id)
            # If Questioning Channel is not existing, cancel
            if not isinstance(questioning_channel, disnake.TextChannel):
                return
            # Generate Transcripts
            transcript = io.BytesIO()
            transcript_wrapper = io.TextIOWrapper(transcript, encoding="utf-8", write_through=True)
            messages = await questioning_channel.history(limit=250).flatten()
            for msg in reversed(messages):
                transcript_wrapper.write(f"{msg.author}: {msg.content} (Sent {msg.created_at})\n")
            await questioning_channel.delete()
            try:
                transcript_wrapper.seek(0)                
                await logging_channel.send(
                    file=disnake.File(transcript, "transcript.txt"),
                    embed=message.embeds[0]
                )
            except:
                # If it fails, send logging channel and that's it
                bot.log.info("Failed to send transcript")
                await logging_channel.send(embed=message.embeds[0])
            finally:
                # Stop the transcripting process
                transcript.close()
        else:
            # Send Logs
            await logging_channel.send(embed=message.embeds[0])
        # Delete from Verification Table
        return await verification.delete()
