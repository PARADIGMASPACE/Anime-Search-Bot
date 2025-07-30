from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Awaitable, Dict, Any
from cache.user_cache import user_cache
from database.users import get_user_language_from_db


class LanguageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        if not user:
            return await handler(event, data)

        user_id = user.id
        lang = await user_cache.get_user_language(user_id)
        if not lang:
            lang = await get_user_language_from_db(user_id)
            if lang:
                await user_cache.user_language(user_id, lang)

        data["lang"] = lang
        return await handler(event, data)
