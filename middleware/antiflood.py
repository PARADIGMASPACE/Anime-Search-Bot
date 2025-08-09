import time
from typing import Dict, Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from loguru import logger

from cache.user_cache import user_cache
from database.users import get_user_language_from_db
from utils.i18n import i18n


class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.user_timeouts: Dict[int, float] = {}

    async def get_user_language(self, user_id: int) -> str:
        try:
            lang = await user_cache.get_user_language(user_id)
            if not lang:
                lang = await get_user_language_from_db(user_id)
                if lang:
                    await user_cache.user_language(user_id, lang)
            return lang or "en"
        except Exception as e:
            logger.error(
                f"Failed to get user language | user_id: {user_id} | error: {e}"
            )
            return "en"

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None

        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id if event.from_user else None

        if user_id is None:
            return await handler(event, data)
        try:
            current_time = time.time()
            last_request_time = self.user_timeouts.get(user_id, 0)

            if current_time - last_request_time < self.rate_limit:
                lang = await self.get_user_language(user_id)
                logger.warning(
                    f"Rate limit triggered | user_id: {user_id} | lang: {lang}"
                )

                if isinstance(event, CallbackQuery):
                    await event.answer(
                        i18n.t("antiflood_middleware.alert", lang=lang), show_alert=True
                    )
                elif isinstance(event, Message):
                    await event.answer(i18n.t("antiflood_middleware.alert", lang=lang))
                    try:
                        await event.delete()
                    except Exception:
                        pass
                return

            self.user_timeouts[user_id] = current_time
            return await handler(event, data)
        except Exception as e:
            logger.error(
                f"Antiflood middleware failed | user_id: {user_id} | error: {e}"
            )
            return await handler(event, data)
