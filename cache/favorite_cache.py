from loguru import logger
from cache.redis_client import redis_client
from typing import List, Dict, Optional


class FavoriteCache:
    def __init__(self):
        self.favorite_ttl = 43200

    def _get_user_favorites_key(self, user_id: int) -> str:
        return f"favorites:{user_id}"

    async def invalidate_user_favorites(self, user_id: int):
        try:
            key = self._get_user_favorites_key(user_id)
            await redis_client.delete(key)
            logger.info(f"Favorite cache has been successfully cleared with key {key}")
        except Exception as e:
            logger.error(f"Error clearing the user's favorites cache: {e}")

    async def cache_user_favorites(self, user_id: int, favorites: List[Dict]):
        try:
            key = self._get_user_favorites_key(user_id)
            await redis_client.set(key, favorites, expire=self.favorite_ttl)
            logger.info(f"Favorite cache has been successfully saved with key {key}")
        except Exception as e:
            logger.error(f"Caching error for selected user: {e}")

    async def get_cached_user_favorites(self, user_id: int) -> Optional[List[Dict]]:
        try:
            key = self._get_user_favorites_key(user_id)
            data = await redis_client.get(key)
            logger.info(f"Favorite cache was successfully retrieved with key {key}")
            return data
        except Exception as e:
            logger.error(f"Error retrieving selected user from cache: {e}")
            return None


favorite_cache = FavoriteCache()
