from typing import List, Dict, Optional, Any
from loguru import logger
from cache.redis_client import redis_client


class AnimeCache:
    def __init__(self):
        self.cache_ttl = 43200
        self.search_ttl = 21600

    def _get_anime_key(self, anime_id: int) -> str:
        return f"anime:{anime_id}"

    def _get_search_key(self, user_id: int, query: str) -> str:
        return f"search:user:{user_id}:{query.lower().replace(' ', '_')}"

    def _get_user_favorites_key(self, user_id: int) -> str:
        return f"favorites:{user_id}"

    def _get_last_msg_key(self, user_id: int) -> str:
        return f"last_bot_msg:{user_id}"

    async def cache_anime(self, shikimori_id: int, caption: str, cover_image: str, anilist_id: int):
        try:
            key = self._get_anime_key(shikimori_id)
            anime_data = {
                "caption": caption,
                "cover_image": cover_image,
                "anilist_id": anilist_id,
                "shikimori_id": shikimori_id
            }
            await redis_client.set(key, anime_data, expire=self.cache_ttl)
        except Exception as e:
            logger.error(f"Ошибка кеширования аниме {shikimori_id}: {e}")

    async def get_cached_anime(self, anime_id: int) -> Optional[Dict[str, Any]]:
        try:
            key = self._get_anime_key(anime_id)
            data = await redis_client.get(key)
            return data
        except Exception as e:
            logger.error(f"Ошибка получения аниме {anime_id} из кеша: {e}")
            return None

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

    async def invalidate_user_search(self, user_id: int, query: str):
        try:
            key = self._get_search_key(user_id, query)
            await redis_client.delete(key)
        except Exception as e:
            logger.error(f"Ошибка очистки кеша поиска для пользователя {user_id}: {e}")

    async def invalidate_user_favorites(self, user_id: int):
        try:
            key = self._get_user_favorites_key(user_id)
            await redis_client.delete(key)
        except Exception as e:
            logger.error(f"Ошибка очистки кеша избранного пользователя {user_id}: {e}")

    async def cache_user_favorites(self, user_id: int, favorites: List[Dict]):
        try:
            key = self._get_user_favorites_key(user_id)
            await redis_client.set(key, favorites, expire=self.cache_ttl)
        except Exception as e:
            logger.error(f"Ошибка кеширования избранного пользователя {user_id}: {e}")

    async def get_cached_user_favorites(self, user_id: int) -> Optional[List[Dict]]:
        try:
            key = self._get_user_favorites_key(user_id)
            data = await redis_client.get(key)
            return data
        except Exception as e:
            logger.error(f"Ошибка получения избранного пользователя {user_id} из кеша: {e}")
            return None

    async def save_user_context(self, user_id: int, context: Dict[str, Any], ttl: int = 1800):
        try:
            key = f"context:{user_id}"
            await redis_client.set(key, context, expire=ttl)
        except Exception as e:
            logger.error(f"Ошибка сохранения контекста пользователя {user_id}: {e}")

    async def get_user_context(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            key = f"context:{user_id}"
            return await redis_client.get(key)
        except Exception as e:
            logger.error(f"Ошибка получения контекста пользователя {user_id}: {e}")
            return None

    async def save_user_last_search(self, user_id: int, query: str, results: List[Dict]):
        try:
            key = f"last_search:{user_id}"
            data = {"query": query, "results": results}
            await redis_client.set(key, data, expire=self.search_ttl)
        except Exception as e:
            logger.error(f"Ошибка сохранения последнего поиска {user_id}: {e}")

    async def get_user_last_search(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            key = f"last_search:{user_id}"
            return await redis_client.get(key)
        except Exception as e:
            logger.error(f"Ошибка получения последнего поиска {user_id}: {e}")
            return None


anime_cache = AnimeCache()
