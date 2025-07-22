import aiohttp
import asyncio
from loguru import logger


async def fetch_json_with_retries(url: str, max_retries: int = 3, backoff_base: int = 2):
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 429:
                        await asyncio.sleep(backoff_base ** attempt)
                        continue
                    if 200 <= resp.status < 300:
                        return await resp.json()
                    else:
                        logger.warning(f"Request failed: {resp.status} — {url}")
        except Exception as e:
            logger.exception(f"Exception on attempt {attempt + 1}: {e}")
        await asyncio.sleep(1)
    return {}


async def get_many_info_about_anime_from_shikimori(query: str):
    url = f"https://shikimori.one/api/animes?search={query}&limit=20"
    return await fetch_json_with_retries(url)


async def get_info_about_anime_from_shikimori_by_id(anime_id: int):
    url = f"https://shikimori.one/api/animes/{anime_id}"
    return await fetch_json_with_retries(url)

