import asyncio

import disnake
from modules.otterverify.database.model import VerificationApp, VerificationGuild
from disnake import Guild
from apgorm.exceptions import ModelNotFound


async def has_verification_open(user_id: int, guild_id: int) -> bool:
    checker = await VerificationApp.find_or_fail(user_id, guild_id)
    return checker is not False


async def get_guild_data(guild_id: int) -> VerificationGuild:
    return await VerificationGuild.fetch(guild_id=guild_id)


async def get_verification(user_id: int) -> VerificationApp:
    return await VerificationApp.fetch(user_id=user_id)


async def create_guilds_data(guilds: list[Guild]) -> int:
    new_guilds = 0
    for guild in guilds:
        try:
            await VerificationGuild.fetch(guild_id=guild.id)
        except (ModelNotFound):
            await VerificationGuild(guild_id=guild.id).create()
            new_guilds += 1
    return new_guilds


async def ask_reason(interaction: disnake.Interaction, button: disnake.Button):
    await interaction.response.send_modal(
        title="Provide Reason",
        custom_id=f"reason_modal:{button.custom_id}",
        components=[
            disnake.ui.TextInput(
                label="Reason",
                placeholder="Brief Description.",
                custom_id="reason",
                style=disnake.TextInputStyle.long,
                max_length=1000,
            ),
        ])
    # Waits until the user submits the modal
    try:
        modal_inter: disnake.ModalInteraction = await interaction.bot.wait_for(
            "modal_submit",
            check=lambda i: i.custom_id == f"reason_modal:{button.custom_id}" and i.author.id == interaction.author.id,
            timeout=300,
        )
        # If Reason is cancel, Cancel
        if modal_inter.text_values['reason'] == "cancel":
            await modal_inter.response.send_message("Cancelled Request", ephemeral=True)
            return
        await modal_inter.response.send_message("Handled Application", ephemeral=True)
        return modal_inter
    except asyncio.TimeoutError:
        return


async def text_reason(message: disnake.Message, reason: str):
    if not reason:
        return await message.channel.send("Please provide a reason along with the command please.")
    return reason

async def get_verif_delete(inter: disnake.MessageInteraction):
    if not inter.guild:
        return
    try:
        data = await VerificationApp.fetch(pending_verification_id=inter.message.id, guild_id=inter.guild.id)
    except ModelNotFound:
        guild_data = await VerificationGuild.fetch(guild_id=inter.guild.id)
        log = inter.guild.get_channel(guild_data.verification_logging_channel) # type: ignore
        await log.send(f"User {inter.author.mention} deleted a verification application that was not found in the database.", embed=inter.message.embeds[0]) # type: ignore
        await inter.response.send_message("Cannot find verification application attached to this message.", ephemeral=True)
        await inter.message.delete()
        return False
    return data
        
    