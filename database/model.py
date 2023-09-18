import apgorm as orm
import disnake
from apgorm.exceptions import ModelNotFound
from apgorm.types import BigInt, Boolean, Array, Text, Serial, Int
from modules.ottermail.database.model import Modmail


class Client(orm.Model):
    id = Int().field()
    client_id = BigInt().field()
    maintenance_mode = Boolean().field(default=False)
    allowed_guilds = Array(BigInt()).field(default=[])
    support_channel_id = BigInt().nullablefield(default=None)
    primary_key = (id,)


class Guild(orm.Model):
    guild_id = BigInt().field()

    primary_key = (guild_id,)
