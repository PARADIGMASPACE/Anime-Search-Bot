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
            logger.info(f"User language saved {key}")
        except Exception:
            logger.error(f"Language caching error {user_id}:{language}")

    async def get_user_language(self, user_id: int) -> str | None:
        try:
            key = self._get_user_language_key(user_id)
            data = await redis_client.get(key)
            logger.info(f"User language received {key}")
            return data
        except Exception as e:
            logger.error(f"Error retrieving language {user_id} from cache: {e}")
            return None


user_cache = UserCache()
