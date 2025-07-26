import time
from typing import Dict, Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery


class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.user_timeouts: Dict[int, float] = {}

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user_id = None

        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id if event.from_user else None

        if user_id is None:
            return await handler(event, data)

        current_time = time.time()
        last_request_time = self.user_timeouts.get(user_id, 0)

        if current_time - last_request_time < self.rate_limit:
            if isinstance(event, CallbackQuery):
                await event.answer("Слишком быстро! Подождите секунду.", show_alert=True)
            elif isinstance(event, Message):
                await event.answer("Слишком быстро! Подождите секунду.", show_alert=True)
                try:
                    await event.delete()
                except Exception:
                    pass
            return

        self.user_timeouts[user_id] = current_time
        return await handler(event, data)
