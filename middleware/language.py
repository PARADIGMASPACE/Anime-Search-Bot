from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Awaitable, Dict, Any

from loguru import logger

from cache.user_cache import user_cache
from database.users import get_user_language_from_db


class LanguageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id

        try:
            lang = await user_cache.get_user_language(user_id)

            if not lang:
                lang = await get_user_language_from_db(user_id)
                if lang:
                    await user_cache.user_language(user_id, lang)
            else:
                logger.debug(
                    f"Language loaded from cache | user_id: {user_id} | lang: {lang}"
                )

            data["lang"] = lang
            return await handler(event, data)
        except Exception as e:
            logger.error(
                f"Language middleware failed | user_id: {user_id} | error: {e}"
            )
            data["lang"] = "en"
            return await handler(event, data)
