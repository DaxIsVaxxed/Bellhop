from enum import Enum
import io
from typing import Optional
import apgorm

import apgorm as orm
from apgorm.exceptions import ModelNotFound
import disnake
from apgorm.types import BigInt, Boolean, Array, Text, Serial

from modules.ottermail.utils.embeds import otter_embed


class ModmailGuild(orm.Model):
    guild_id = BigInt().field()
    # Modmail Configuration
    modmail_category_id = BigInt().nullablefield(default=None)
    modmail_log_channel_id = BigInt().nullablefield(default=None)
    modmail_instruction = Text().nullablefield(default=None)
    modmail_staff_role_id = BigInt().nullablefield(default=None)
    
    primary_key = (guild_id,)
    
class Modmail(orm.Model):
    id = Serial().field()
    # Way to identify the modmail
    user_id = BigInt().field()
    guild_id = BigInt().field()
    modmail_channel_id = BigInt().field()
    no_dm = Boolean().field(default=False)

    primary_key = (id,)

    @staticmethod
    async def find_or_fail_bcid(channel_id: int):
        try:
            modmail = await Modmail.fetch(modmail_channel_id=channel_id)
        except ModelNotFound:
            return False
        return modmail

    @staticmethod
    async def find_or_fail_buid(user_id: int):
        try:
            modmail = await Modmail.fetch(user_id=user_id)
        except ModelNotFound:
            return False
        return modmail

    @staticmethod
    async def close_modmail(guild: disnake.Guild, user: disnake.User,
                        channel: disnake.TextChannel) -> None:
        embed = otter_embed(user)
        embed.add_field(name="User", value=user.name)
        embed.title = "Closed Modmail"

        messages = await channel.history(limit=250).flatten()
        messages.reverse()

        transcript_file = io.StringIO()
        for msg in messages:
            transcript_file.write(f"{msg.author}: {msg.content} (Sent {msg.created_at})\n")

        await channel.delete()

        guild_data = await ModmailGuild.fetch(guild_id=guild.id)
        log_channel = guild.get_channel(guild_data.modmail_log_channel_id)

        transcript_file.seek(0)
        with io.BytesIO(transcript_file.getvalue().encode()) as buffer:
            await log_channel.send(
                file=disnake.File(buffer, "transcript.txt"),
                embed=embed
            )

        modmail = await Modmail.fetch(user_id=user.id)
        await modmail.delete()
