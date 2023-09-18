import os

def load_cogs(bot):
    bot.logger.info("Loading cogs...")
    for files in os.listdir("cogs"):
        if files.endswith(".py"):
            try:
                bot.load_extension(f"cogs.{files[:-3]}")
            except Exception as e:
                bot.logger.error(f"Failed to load {files}", exc_info=True)
            bot.logger.info(f"Loaded cog: {files[:-3]}")