import disnake


class AddRemoveMenu(disnake.ui.View):

    def __init__(self):
        super().__init__()
        self.method = None

    @disnake.ui.button(label="Add", style=disnake.ButtonStyle.green)
    async def confirm(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.defer()
        self.method = "add"
        self.stop()
        return

    @disnake.ui.button(label="Remove", style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.defer()
        self.method = "remove"
        self.stop()
        return

    @disnake.ui.button(label="Done", style=disnake.ButtonStyle.blurple)
    async def done(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.defer()
        self.method = "finish"
        self.stop()
        return
