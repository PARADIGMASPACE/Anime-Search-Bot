from aiogram import types
from utils.i18n import i18n


commands = [
    types.BotCommand(command="start", description=i18n.t("commands_bot.start")),
    types.BotCommand(command="favorites", description=i18n.t("commands_bot.favorites")),
    types.BotCommand(command="language", description=i18n.t("commands_bot.language"))
]
