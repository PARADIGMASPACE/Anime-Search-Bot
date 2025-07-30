from loguru import logger
from cache.redis_client import redis_client


class UserCache:
    def __init__(self):
        self.user_tll = 43200

    def _get_user_language_key(self, user_id: int) -> str:
        return f"language:{user_id}"

    async def user_language(self, user_id: int, language: str):
        try:
            key = self._get_user_language_key(user_id)
            await redis_client.set(key, language, expire=self.user_tll)
        except Exception as e:
            logger.error(f"Ошибка кеширования языка {user_id}:{language}")

    async def get_user_language(self, user_id: int) -> str | None:
        try:
            key = self._get_user_language_key(user_id)
            data = await redis_client.get(key)
            return data
        except Exception as e:
            logger.error(f"Ошибка получения языка {user_id} из кеша: {e}")
        return None

user_cache = UserCache()