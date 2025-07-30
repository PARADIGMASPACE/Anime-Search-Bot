from loguru import logger
from cache.redis_client import redis_client
from typing import List, Dict, Optional, Any


class SearchCache:
    def __init__(self):
        self.search_ttl = 21600

    def _get_search_key(self, user_id: int, query: str) -> str:
        return f"search:user:{user_id}:{query.lower().replace(' ', '_')}"

    def _get_last_search_key(self, user_id: int) -> str:
        return f"last_search:{user_id}"

    async def cache_search_results(self, user_id: int, query: str, results: List[Dict]):
        try:
            key = self._get_search_key(user_id, query)
            search_data = {
                'query': query,
                'results': results
            }
            await redis_client.set(key, search_data, expire=self.search_ttl)
        except Exception as e:
            logger.error(f"Ошибка кеширования поиска '{query}' для пользователя {user_id}: {e}")

    async def get_cached_search_results(self, user_id: int, query: str) -> Optional[Dict[str, Any]]:
        try:
            key = self._get_search_key(user_id, query)
            data = await redis_client.get(key)
            return data
        except Exception as e:
            logger.error(f"Ошибка получения поиска '{query}' для пользователя {user_id} из кеша: {e}")
            return None

    async def get_user_last_search(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            key = self._get_last_search_key(user_id)
            return await redis_client.get(key)
        except Exception as e:
            logger.error(f"Ошибка получения последнего поиска {user_id}: {e}")
            return None

    async def save_user_last_search(self, user_id: int, query: str, results: List[Dict]):
        try:
            key = f"last_search:{user_id}"
            data = {"query": query, "results": results}
            await redis_client.set(key, data, expire=self.search_ttl)
        except Exception as e:
            logger.error(f"Ошибка сохранения последнего поиска {user_id}: {e}")


search_cache = SearchCache()
