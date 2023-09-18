import logging

import disnake
from disnake.ext import commands

from database.database import setup_database
from utils.db_starting import create_client
from utils.load_cogs import load_cogs
from utils.logger import setup_logger
from utils.presence import change_status
from modules.otterverify import Verification
from modules.ottereco import Economy
from modules.otterbot import OtterBot
from modules.ottermail import Modmail
from modules.otterverify.cogs.verification import ActionButton, VerifyButton
from modules.ottermail.cogs.modmail import ModmailButton
from modules.otterleveling import Leveling
from utils.setup_config import get_config
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

cfg = get_config()


class OtterClient(commands.Bot):
    def __init__(self):
        test_guilds = cfg["dev_guilds"] if cfg["dev_mode"] else cfg["guilds"]
        super().__init__(
            test_guilds=test_guilds,
            command_prefix=cfg["command_prefix"],
            intents=disnake.Intents.all(),
        )
        # Sets config to the bot props
        self.config = cfg
        # Setup Props
        self.cogs_loaded = False
        self.persistent_views_loaded = False
        self.scheduler: AsyncIOScheduler | None = None
        self.schedule_loaded = False
        # Database URL
        self.database_url = f"postgresql+asyncpg://{self.config['database']['user']}:" \
                            f"{self.config['database']['password']}@{self.config['database']['host']}" \
                            f":{self.config['database']['port']}/{self.config['database']['database']}"
        # Initialize Loggers
        self.logger = setup_logger()
        self.log = logging.getLogger("Bot")
        self.log.setLevel(logging.INFO)
        self.discord_log = logging.getLogger("discord")
        self.discord_log.setLevel(logging.INFO)
        self.color = disnake.Color.purple()
        # Initalize Plugins
        self.verification = Verification(self)
        self.base_module = OtterBot(self)
        self.economy_module = Economy(self)
        self.ottermail = Modmail(self)
        self.otterlevels = Leveling(self)
        self.economy_cooldowns = {}
        self.xp_cooldown = {}
        self.loaded_plugins = []

        @self.event
        async def on_ready():
            # Setups Database
            await setup_database(self)
            # Fancy Start Screen
            self.log.info(f"##############################")
            self.log.info(f"User: {self.user}")
            self.log.info(f"Guild count: {len(self.guilds)}")
            self.log.info(f"User count: {len(self.users)}")
            self.log.info(f"##############################")

            # Changes Bot Presences
            await change_status(self, disnake.Status.dnd, disnake.ActivityType.playing, f"Bot is starting....")

            # TESTING
            # self.verification.get_config_categories()
            # print(self.verification.get_config_category("VERIFICATION"))


            # TODO" Uncomment if database needed
            self.log.info("Getting/Creating Client Data from DB")
            client = await create_client(self.user.id)
            # self.log.info("Adding new users to the Database")
            # users = await create_users(self.users)
            # self.log.info("Adding new guilds to the Database")
            # guilds = await create_guilds(self.guilds)
            # self.log.info(f"Added {guilds} new guilds")
            self.log.info(f"##############################")
            if not self.cogs_loaded:
                self.logger.info("Loading Cogs & Plugins")
                load_cogs(self)
                await self.verification.enable_plugin()
                await self.base_module.enable_plugin()
                await self.economy_module.enable_plugin()
                await self.ottermail.enable_plugin()
                await self.otterlevels.enable_plugin()
                self.logger.info("Loaded Cogs")
                self.cogs_loaded = True
            if not self.persistent_views_loaded:
                self.logger.info("Loading persistent views...")
                # TODO: Add any presisent views (if appliciable)
                self.add_view(VerifyButton())
                self.add_view(ActionButton())
                self.add_view(ModmailButton())
                self.logger.info("Loaded persistent views.")
            # TODO: Uncomment if you plan to use a schedule system
            if not self.schedule_loaded:
                self.logger.info("Loading schedule...")
                job_store = {}
                for guild in self.guilds:
                    job_store[guild.id] = SQLAlchemyJobStore(url=self.database_url)
                self.scheduler = AsyncIOScheduler()
                self.scheduler.start()
                self.schedule_loaded = True
                self.logger.info("Loaded schedule.")
                await self.economy_module.start_bot_tasks()
                await self.otterlevels.start_bot_tasks()
            guilds = self.config["dev_guilds"] if self.config["dev_mode"] else self.config["guilds"]
            temp = 0
            for guild in guilds:
                real_guild = self.get_guild(guild)
                if not real_guild:
                    continue
                temp += len(real_guild.members)
            await change_status(self, disnake.Status.online, disnake.ActivityType.playing, f"with {temp} users!")
            self.logger.info("Bot is ready.")


if __name__ == '__main__':
    client = OtterClient()
    client.run(client.config["token"] if not client.config["dev_mode"] else client.config["dev_token"])
