from typing import Dict, Optional, Any
from loguru import logger
from cache.redis_client import redis_client


class AnimeCache:
    def __init__(self):
        self.anime_ttl = 43200

    def _get_anime_key(self, shikimori_id: int, lang: str = "en") -> str:
        return f"anime:{shikimori_id}:{lang}"

    async def cache_anime(
        self,
        shikimori_id: int,
        caption: str,
        cover_image: str,
        anilist_id: int,
        raw_data_db: dict,
        lang: str = "en",
    ):
        try:
            key = self._get_anime_key(shikimori_id, lang)
            anime_data = {
                "caption": caption,
                "cover_image": cover_image,
                "anilist_id": anilist_id,
                "shikimori_id": shikimori_id,
                "raw_data_db": raw_data_db,
                "lang": lang,
            }
            await redis_client.set(key, anime_data, expire=self.anime_ttl)
            logger.info(f"Save anime data with key {key}")
        except Exception as e:
            logger.error(f"Error while caching: {e}")

    async def get_cached_anime(
        self, shikimori_id: int, lang: str = "en"
    ) -> Optional[Dict[str, Any]]:
        try:
            key = self._get_anime_key(shikimori_id, lang)
            data = await redis_client.get(key)
            logger.info(f"The anime date was successfully obtained with key {key}")
            return data
        except Exception as e:
            logger.error(f"Error reading anime cache\nException: {e}")
            return None


anime_cache = AnimeCache()
