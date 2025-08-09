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
            search_data = {"query": query, "results": results}
            await redis_client.set(key, search_data, expire=self.search_ttl)
            logger.info(f"Search cache has been successfully saved {key}")
        except Exception as e:
            logger.error(f"Error caching search ‘{query}’ for user {user_id}: {e}")

    async def get_cached_search_results(
        self, user_id: int, query: str
    ) -> Optional[Dict[str, Any]]:
        try:
            key = self._get_search_key(user_id, query)
            data = await redis_client.get(key)
            logger.info(f"Cache was received successfully {key}")
            return data
        except Exception as e:
            logger.error(
                f"Error retrieving search ‘{query}’ for user {user_id} from cache: {e}"
            )
            return None

    async def get_user_last_search(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            key = self._get_last_search_key(user_id)
            logger.info(f"Last user search received successfully {key}")
            return await redis_client.get(key)
        except Exception as e:
            logger.error(f"Error retrieving last search {user_id}: {e}")
            return None

    async def save_user_last_search(
        self, user_id: int, query: str, results: List[Dict]
    ):
        try:
            key = self._get_last_search_key(user_id)
            data = {"query": query, "results": results}
            await redis_client.set(key, data, expire=self.search_ttl)
            logger.info(f"The latest search results have been saved successfully {key}")
        except Exception as e:
            logger.error(f"Error saving last search {user_id}: {e}")


search_cache = SearchCache()
