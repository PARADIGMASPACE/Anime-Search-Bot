from aiogram import types
from utils.i18n import i18n


commands_ru = [
    types.BotCommand(command="start", description=i18n.t("commands_bot.start", lang="ru")),
    types.BotCommand(command="favorites", description=i18n.t("commands_bot.favorites", lang="ru")),
    types.BotCommand(command="language", description=i18n.t("commands_bot.language", lang="ru")),
]

commands_en = [
    types.BotCommand(command="start", description=i18n.t("commands_bot.start", lang="en")),
    types.BotCommand(command="favorites", description=i18n.t("commands_bot.favorites", lang="en")),
    types.BotCommand(command="language", description=i18n.t("commands_bot.language", lang="en")),
]
