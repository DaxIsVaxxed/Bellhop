import apgorm
from disnake import Guild as DiscordGuild
from disnake import User as DiscordUser

from database.model import Guild, Client


# async def create_users(users: list[DiscordUser]):
#     userCount = 0
#     for user in users:
#         try:
#             await User.fetch(id=user.id)
#         except apgorm.exceptions.ModelNotFound:
#             await User(id=user.id).create()
#             userCount += 1
#     return userCount


async def create_guilds(guilds: list[DiscordGuild]):
    guildCount = 0
    for guild in guilds:
        try:
            await Guild.fetch(guild_id=guild.id)
        except apgorm.exceptions.ModelNotFound:
            await Guild(guild_id=guild.id).create()
            guildCount += 1
    return guildCount

async def create_client(id: int):
    try:
        await Client.fetch(id=1, client_id=id)
    except apgorm.exceptions.ModelNotFound:
        await Client(id=1, client_id=id).create()
    return Client