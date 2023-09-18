import disnake



async def change_status(bot, status: disnake.Status, type: disnake.ActivityType, msg: str):
    await bot.change_presence(
        activity=disnake.Activity(
            name=msg,
            type=type
        ),
        status=status
    )
