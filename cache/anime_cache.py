from typing import Dict, Optional, Any
from loguru import logger
from cache.redis_client import redis_client


class AnimeCache:
    def __init__(self):
        self.anime_ttl = 43200

    def _get_anime_key(self, anime_id: int) -> str:
        return f"anime:{anime_id}"

    async def cache_anime(self, shikimori_id: int, caption: str, cover_image: str, anilist_id: int):
        try:
            key = self._get_anime_key(shikimori_id)
            anime_data = {
                "caption": caption,
                "cover_image": cover_image,
                "anilist_id": anilist_id,
                "shikimori_id": shikimori_id
            }
            await redis_client.set(key, anime_data, expire=self.anime_ttl)
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


anime_cache = AnimeCache()
