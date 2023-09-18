import apgorm
import json

import asyncpg
from modules.ottereco.database.model import EconomyRoleIncome, EconomyRoleMultplier, PurchasableRole, EconomyGuild, EconomyUser

from database.model import Guild, Client
from modules.otterverify.database.model import VerificationApp, VerificationStatus, VerificationGuild
from modules.ottermail.database.model import Modmail, ModmailGuild
from modules.otterleveling import Leveling, LevelingGuild, LevelRoleMultplier, LevelRoles, LevelUsers

with open("config/config.json") as f:
    db_config = json.load(f)["database"]


class Database(apgorm.Database):
    # DEFAULT MODELS
    guilds = Guild
    client = Client
    # OTTER VERIFY
    verification_guild = VerificationGuild
    verification_app = VerificationApp
    verification_status = VerificationStatus
    ########### ECONOMY PLUGIN ###########
    economy_role_income = EconomyRoleIncome
    economy_role_multiplier = EconomyRoleMultplier
    purchasable_role = PurchasableRole
    economy_guild = EconomyGuild
    economy_user = EconomyUser
    ########### MODMAIL PLUGIN ###########
    modmail = Modmail
    modmail_guild = ModmailGuild
    ########### LEVELING PLUGIN ###########
    leveling = Leveling
    leveling_guild = LevelingGuild
    leveling_role_multiplier = LevelRoleMultplier
    leveling_roles = LevelRoles
    leveling_user = LevelUsers
    




async def setup_database(bot):
    bot.log.info("Connecting to the Database")
    # Create Database if it doesn't exist
    db = await asyncpg.connect(
        host=db_config["host"],
        port=db_config["port"],
        user=db_config["user"],
        password=db_config["password"]
    )
    try:
        await db.execute(f"CREATE DATABASE {db_config['database']}")
    except asyncpg.exceptions.DuplicateDatabaseError:
        pass
    await db.close()
    # Set up the ORM
    db = Database("database/database/migrations")
    await db.connect(**db_config)
    if db.must_create_migrations():
        bot.log.info("Creating Database Migration")
        db.create_migrations()
    if await db.must_apply_migrations():
        bot.log.info("Applying Database Migration")
        await db.apply_migrations()
        bot.log.info("Database Migration Applied")
