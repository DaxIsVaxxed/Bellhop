from datetime import datetime

import disnake
from disnake import Embed


class otter_embed(Embed):
    def __init__(self, author: disnake.User | disnake.Member):
        super().__init__()
        self.set_author(
            name=author.name,
            icon_url=author.display_avatar,
        )
        self.color = self.set_default_color(0x8800ff)
        self.timestamp = datetime.now()
        self.set_footer(
            text=f"User ID: {author.id}",
            icon_url=author.display_avatar
        )

