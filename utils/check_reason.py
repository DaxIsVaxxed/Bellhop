import disnake
import asyncio


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
    # Waits until the user submits the modal.
    try:
        modal_inter: disnake.ModalInteraction = await interaction.bot.wait_for(
            "modal_submit",
            check=lambda i: i.custom_id == f"reason_modal:{button.custom_id}" and i.author.id == interaction.author.id,
            timeout=300,
        )
        if modal_inter.text_values['reason'] == "cancel":
            await modal_inter.response.send_message("Cancelled Request", ephemeral=True)
            return
        await modal_inter.response.send_message("Handled Application", ephemeral=True)
        return modal_inter
    except asyncio.TimeoutError:
        return