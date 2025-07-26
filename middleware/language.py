from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from database.users import get_user_language
from utils.i18n import i18n

class LanguageMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user_id = None

        if hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id

        if user_id:
            user_language = await get_user_language(user_id)
            if user_language:
                i18n.default_lang = user_language

        return await handler(event, data)
