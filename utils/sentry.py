import sentry_sdk
from disnake.ext.commands import Context


def log_exception(bot, exception=None, ctx: Context = None):
    if bot.config['sentry_dsn'] is None:
        return

    with sentry_sdk.push_scope() as scope:
        if ctx:
            scope.user = {"id": ctx.author.id, "username": str(ctx.author)}
            scope.set_tag("message.content", ctx)
            scope.set_tag("is_private_message", ctx.guild is None)
            scope.set_tag("channel.id", ctx.channel.id)
            scope.set_tag("channel.name", str(ctx.channel))
            if ctx.guild is not None:
                scope.set_tag("guild.id", ctx.guild.id)
                scope.set_tag("guild.name", str(ctx.guild))
        sentry_sdk.capture_exception(exception) 