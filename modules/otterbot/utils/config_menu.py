import asyncio
from builtins import setattr

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext.commands import GuildChannelConverter, CategoryChannelConverter, RoleConverter
from disnake.ext.commands.context import Context
from disnake.ext.commands.errors import CommandError, BadArgument

from modules.otterbot.utils.add_remove_menu import AddRemoveMenu
from modules.otterbot.utils.embeds import otter_embed


class ConfigCategoryDropdown(disnake.ui.Select):
    def __init__(self, ctx: ApplicationCommandInteraction, categories: list[str], plugin):
        self.ctx = ctx
        self.plugin = plugin
        super().__init__(
            custom_id="config-menu",
            placeholder="Select an Category...",
            options=[disnake.SelectOption(
                label=category,
                value=category,
                description=f"Configure stuff related to {category}."
            ) for category in categories],
        )

    async def callback(self, interaction: disnake.ApplicationCommandInteraction):
        options = self.plugin.get_config_category_with_description(self.values[0])
        settings_menu = SettingCategoryView(interaction, options, self.values[0], self.plugin)
        embed = otter_embed(interaction.author)
        embed.title = "Verification Settings"
        embed.description = "Configure the Verification settings."
        for value in options.values():
            embed.add_field(
                name=value,
                value=f"Configure the {value}.",
                inline=False
            )
        await interaction.response.send_message(embed=embed, view=settings_menu)
        pass

class ConfigCategoryDropdownView(disnake.ui.View):
    def __init__(self, ctx: Context, categories: list[str], plugin):
        super().__init__()
        self.plugin = plugin
        self.add_item(ConfigCategoryDropdown(ctx, categories, plugin))


class SettingCategoryDropdown(disnake.ui.Select):
    def __init__(self, ctx: Context, settings: dict[str, str], category, plugin):
        self.ctx = ctx
        self.category = category
        self.plugin = plugin
        super().__init__(
            custom_id="settings-menu",
            placeholder="Select an Setting...",
            options=[disnake.SelectOption(
                label=value,
                value=key,
            ) for key, value in settings.items()],
        )

    async def callback(self, interaction: disnake.MessageInteraction):
        def check_message(message: disnake.Message):
            return message.author.id == interaction.user.id and interaction.channel.id == message.channel.id

        guild_data = await self.plugin.get_guild_configurations(interaction.guild.id)
        type = self.plugin.get_config_category_setting_type(self.category, self.values[0])

        match(type):
            case "CHANNEL":
                msg = await interaction.response.send_message("Please send a channel you would like to use?")
                try:
                    channel: disnake.Message = await self.ctx.bot.wait_for(event="message", check=check_message,
                                                                           timeout=120)
                except asyncio.TimeoutError:
                    return await msg.channel.send("❌ Took too long. ")
                if channel.content:
                    converter = GuildChannelConverter()
                    try:
                        value = await converter.convert(self.ctx, channel.content)
                    except (BadArgument, CommandError):
                        return await channel.add_reaction("❌")
                    setattr(guild_data, self.values[0], value.id)
                    await guild_data.save()
                    return await channel.add_reaction("✅")
                return
            case "CHANNEL_CATEGORY":
                msg = await interaction.response.send_message("Please send a channel category you would like to use?")
                try:
                    category: disnake.Message = await self.ctx.bot.wait_for(event="message", check=check_message,
                                                                            timeout=120)
                except asyncio.TimeoutError:
                    return await msg.channel.send("❌ Took too long. ")
                if category.content:
                    converter = CategoryChannelConverter()
                    try:
                        value = await converter.convert(self.ctx, category.content)
                    except (BadArgument, CommandError):
                        return await category.add_reaction("❌")
                    setattr(guild_data, self.values[0], value.id)
                    await guild_data.save()
                    return await category.add_reaction("✅")
                return
            case "BOOLEAN":
                msg = await interaction.response.send_message("Please send 'true' or 'false' for the boolean value?")
                try:
                    boolean: disnake.Message = await self.ctx.bot.wait_for(event="message", check=check_message,
                                                                           timeout=120)
                except asyncio.TimeoutError:
                    return await msg.channel.send("❌ Took too long. ")
                if boolean.content.lower() in ["true", "false"]:
                    value = True if boolean.content.lower() == "true" else False
                    setattr(guild_data, self.values[0], value)
                    await guild_data.save()
                    return await boolean.add_reaction("✅")
                else:
                    return await boolean.add_reaction("❌")
            case "NUMBER":
                msg = await interaction.response.send_message("Please send a number?")
                try:
                    number: disnake.Message = await self.ctx.bot.wait_for(event="message", check=check_message,
                                                                          timeout=120)
                except asyncio.TimeoutError:
                    return await msg.channel.send("❌ Took too long. ")
                if number.content.isdigit():
                    value = int(number.content)
                    setattr(guild_data, self.values[0], value)
                    await guild_data.save()
                    return await number.add_reaction("✅")
                else:
                    return await number.add_reaction("❌")
            case "FLOAT":
                msg = await interaction.response.send_message("Please send a number?")
                try:
                    number: disnake.Message = await self.ctx.bot.wait_for(event="message", check=check_message,
                                                                          timeout=120)
                except asyncio.TimeoutError:
                    return await msg.channel.send("❌ Took too long. ")
                if number.content.replace(".", "", 1).isdigit():
                    value = float(number.content)
                    setattr(guild_data, self.values[0], value)
                    await guild_data.save()
                    return await number.add_reaction("✅")
                else:
                    return await number.add_reaction("❌")
            case "ROLE_LIST":
                done = False
                while not done:
                    roles_data = getattr(guild_data, self.values[0])
                    embed = otter_embed(interaction.user)
                    embed.title = f"List of {self.values[0]}"
                    if roles_data:
                        for data in roles_data:
                            real_role = interaction.guild.get_role(data)
                            embed.add_field(
                                name=real_role.name,
                                value=f"Role Index: {roles_data.index(real_role.id)}",
                                inline=False
                            )
                    else:
                        embed.description = "No roles found."
                    menu = AddRemoveMenu()
                    await interaction.channel.send(embed=embed, view=menu)
                    await menu.wait()
                    match menu.method:
                        case "add":
                            msg = await interaction.channel.send(
                                "Please send the message you would like to add?")
                            try:
                                message: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                                       check=check_message,
                                                                                       timeout=120)
                            except asyncio.TimeoutError:
                                return await msg.channel.send("❌ Took too long to respond. Cancelling.")
                            if message.content:
                                converter = RoleConverter()
                                try:
                                    value = await converter.convert(self.ctx, message.content)
                                except (BadArgument, CommandError):
                                    return await msg.channel.send("❌ Invalid role. Cancelling.")
                                data = getattr(guild_data, self.values[0])
                                data.append(value.id)
                                setattr(guild_data, self.values[0], data)
                                await guild_data.save()
                                await message.add_reaction("✅")
                                continue
                            pass
                        case "remove":
                            msg = await interaction.channel.send(
                                "Please send the index of the role you would like to remove?")
                            try:
                                message: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                                       check=check_message,
                                                                                       timeout=120)
                            except asyncio.TimeoutError:
                                return await msg.channel.send("❌ No response received. Cancelling.")
                            if message.content:
                                data = getattr(guild_data, self.values[0])
                                try:
                                    data.pop(int(message.content))
                                except IndexError:
                                    return await message.add_reaction("❌")
                                except ValueError:
                                    return await message.add_reaction("❌")
                                setattr(guild_data, self.values[0], data)
                                await guild_data.save()
                                await message.add_reaction("✅")
                                continue
                            pass
                        case "edit":
                            msg = await interaction.channel.send(
                                "Please send the index of the role you would like to edit?")
                            try:
                                message: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                                       check=check_message,
                                                                                       timeout=120)
                            except asyncio.TimeoutError:
                                return await msg.channel.send("❌ No response received. Cancelling.")
                            try:
                                index = int(message.content)
                            except ValueError:
                                await msg.channel.send("❌ Invalid Index Cancelling...")
                                return
                            if message.content and index >= 0:
                                data = getattr(guild_data, self.values[0])
                                role_msg = await interaction.channel.send("Please send the new role you would like to use?")
                                try:
                                    role: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                                           check=check_message,
                                                                                           timeout=120)
                                except asyncio.TimeoutError:
                                    return await role_msg.channel.send("❌ No response received. Cancelling.")
                                if role.content:
                                    converter = RoleConverter()
                                    try:
                                        value = await converter.convert(self.ctx, role.content)
                                    except (BadArgument, CommandError):
                                        return await role_msg.channel.send("❌ Invalid role. Cancelling.")
                                    data[int(message.content)] = value.id
                                    setattr(guild_data, self.values[0], data)
                                    await guild_data.save()
                                    await role.add_reaction("✅")
                                    continue
                            else:
                                await message.add_reaction("❌")
                            pass
                        case "finish":
                            done = True
                            return await interaction.channel.send("Finished.")
                    return
                return
            case "ROLE":
                msg = await interaction.response.send_message(
                    "Please send the Role ID/Name/Mention of the role you would like to use?")
                try:
                    role: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                        check=check_message,
                                                                        timeout=120)
                except asyncio.TimeoutError:
                    return await msg.channel.send("❌ No response received. Cancelling.")
                if role.content:
                    converter = RoleConverter()
                    try:
                        value = await converter.convert(self.ctx, role.content)
                    except (BadArgument, CommandError):
                        return await role.channel.send("❌ Invalid role. Cancelling.")
                    setattr(guild_data, self.values[0], value.id)
                    await guild_data.save()
                    return await role.add_reaction("✅")
                return
            case "MESSAGE":
                message = await interaction.response.send_message(
                    "Please send the message that you want sent?\n\n**For welcome messages**: Use %members placeholder to "
                    "display member count\n%user for user being welcomed\n%guild to reference the guild")
                try:
                    msg: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                       check=check_message,
                                                                       timeout=120)
                except asyncio.TimeoutError:
                    return await message.channel.send("❌ Took too long to respond. Cancelling.")
                if msg.content:
                    setattr(guild_data, self.values[0], msg.content)
                    await guild_data.save()
                    return await msg.add_reaction("✅")
                return
            case "MESSAGE_LIST":
                done = False
                while not done:
                    questions = getattr(guild_data, self.values[0])
                    embed = otter_embed(interaction.user)
                    embed.title = f"List of {self.values[0]}"
                    if questions:
                        for question in questions:
                            embed.add_field(
                                name=question,
                                value=f"Question Index: {questions.index(question)}",
                                inline=False
                            )
                    else:
                        embed.description = "No questions found."
                    menu = AddRemoveMenu()
                    await interaction.channel.send(embed=embed, view=menu)
                    await menu.wait()
                    match menu.method:
                        case "add":
                            msg = await interaction.channel.send(
                                "Please send the message you would like to add? (Please keep it 40 Characters or lower)")
                            try:
                                message: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                                       check=check_message,
                                                                                       timeout=120)
                            except asyncio.TimeoutError:
                                await msg.channel.send("❌ Took too long to respond. Cancelling.")
                                return
                            if message.content and len(message.content) <= 40:
                                data = getattr(guild_data, self.values[0])
                                data.append(message.content)
                                setattr(guild_data, self.values[0], data)
                                await guild_data.save()
                                await message.add_reaction("✅")
                                continue
                            pass
                        case "remove":
                            msg = await interaction.channel.send(
                                "Please send the message you would like to remove?")
                            try:
                                message: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                                       check=check_message,
                                                                                       timeout=120)
                            except asyncio.TimeoutError:
                                await msg.channel.send("❌ Took too long to respond. Cancelling.")
                                return
                            if message.content and int(message.content) >= 0:
                                data = getattr(guild_data, self.values[0])
                                try:
                                    data.pop(int(message.content))
                                except IndexError:
                                    return await message.add_reaction("❌")
                                setattr(guild_data, self.values[0], data)
                                await guild_data.save()
                                await message.add_reaction("✅")
                                continue
                            pass
                        case "edit":
                            msg = await interaction.channel.send(
                                "Please send the index of the message you would like to edit?")
                            try:
                                message: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                                       check=check_message,
                                                                                       timeout=120)
                            except asyncio.TimeoutError:
                                await msg.channel.send("❌ Took too long to respond. Cancelling.")
                                return
                            try:
                                index = int(message.content)
                            except ValueError:
                                await msg.channel.send("❌ Invalid Index Cancelling...")
                                return
                            if message.content and index >= 0:
                                data = getattr(guild_data, self.values[0])
                                ask_new_msg = await interaction.channel.send("Please send the new message you would like to replace with instead?")
                                try:
                                    new_msg: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                                           check=check_message,
                                                                                           timeout=120)
                                except asyncio.TimeoutError:
                                    await ask_new_msg.channel.send("❌ Took too long to respond. Cancelling.")
                                    return
                                if new_msg.content and len(new_msg.content) <= 40:
                                    data[int(message.content)] = new_msg.content
                                    setattr(guild_data, self.values[0], data)
                                    await guild_data.save()
                                    await new_msg.add_reaction("✅")
                                    continue
                                else:
                                    await new_msg.add_reaction("❌")
                                    continue
                            else:
                                await message.add_reaction("❌")
                        case "finish":
                            done = True
                            await interaction.channel.send("Finished.")
                    return
                return
            case "TEXT_LIST":
                done = False
                while not done:
                    questions = getattr(guild_data, self.values[0])
                    embed = otter_embed(interaction.user)
                    embed.title = f"List of {self.values[0]}"
                    if questions:
                        for question in questions:
                            embed.add_field(
                                name=question,
                                value=f"Text Index: {questions.index(question)}",
                                inline=False
                            )
                    else:
                        embed.description = "No Texts found."
                    menu = AddRemoveMenu()
                    await interaction.channel.send(embed=embed, view=menu)
                    await menu.wait()
                    match menu.method:
                        case "add":
                            msg = await interaction.channel.send(
                                "Please send the message you would like to add?")
                            try:
                                message: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                                       check=check_message,
                                                                                       timeout=120)
                            except asyncio.TimeoutError:
                                await msg.channel.send("❌ Took too long to respond. Cancelling.")
                                return
                            if message.content:
                                data = getattr(guild_data, self.values[0])
                                data.append(message.content)
                                setattr(guild_data, self.values[0], data)
                                await guild_data.save()
                                await message.add_reaction("✅")
                                continue
                            pass
                        case "remove":
                            msg = await interaction.channel.send(
                                "Please send the message you would like to remove?")
                            try:
                                message: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                                       check=check_message,
                                                                                       timeout=120)
                            except asyncio.TimeoutError:
                                await msg.channel.send("❌ Took too long to respond. Cancelling.")
                                return
                            if message.content and int(message.content):
                                data = getattr(guild_data, self.values[0])
                                try:
                                    data.pop(int(message.content))
                                except IndexError:
                                    return await message.add_reaction("❌")
                                setattr(guild_data, self.values[0], data)
                                await guild_data.save()
                                await message.add_reaction("✅")
                                continue
                            pass
                        case "edit":
                            msg = await interaction.channel.send(
                                "Please send the index of the message you would like to edit?")
                            try:
                                message: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                                       check=check_message,
                                                                                       timeout=120)
                            except asyncio.TimeoutError:
                                await msg.channel.send("❌ Took too long to respond. Cancelling.")
                                return
                            if message.content and int(message.content):
                                data = getattr(guild_data, self.values[0])
                                ask_new_msg = await interaction.channel.send("Please send the new message you would like to replace with instead?")
                                try:
                                    new_msg: disnake.Message = await self.ctx.bot.wait_for(event="message",
                                                                                           check=check_message,
                                                                                           timeout=120)
                                except asyncio.TimeoutError:
                                    await ask_new_msg.channel.send("❌ Took too long to respond. Cancelling.")
                                    return
                                if new_msg.content and len(new_msg.content):
                                    data[int(message.content)] = new_msg.content
                                    setattr(guild_data, self.values[0], data)
                                    await guild_data.save()
                                    await new_msg.add_reaction("✅")
                                    continue
                                else:
                                    await new_msg.add_reaction("❌")
                                    continue
                        case "finish":
                            done = True
                            await interaction.channel.send("Finished.")
                    return
                return





class SettingCategoryView(disnake.ui.View):
    def __init__(self, interaction: ApplicationCommandInteraction, categories: dict[str, str], category, plugin):
        super().__init__()
        self.add_item(SettingCategoryDropdown(interaction, categories, category, plugin))


