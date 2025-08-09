import asyncio
import aiohttp
from loguru import logger
from utils.utils import log_api_response

_ANILIST_QUERY = """
    query ($id: Int) {
      Media(id: $id, type: ANIME) {
        id
        title {
          native
          romaji
          english
        }
        description(asHtml: false)
        coverImage {
          extraLarge
        }
        averageScore
        episodes
        status
        genres
        duration
        type
        startDate {
          year
          month
          day
        }
        airingSchedule(perPage: 100) {
          nodes {
            episode
            airingAt
          }
        }
      }
    }
"""

_ANILIST_QUERY_BY_MAL_ID = """
    query ($idMal: Int) {
      Media(idMal: $idMal, type: ANIME) {
        id
        title {
          native
          romaji
          english
        }
        description(asHtml: false)
        coverImage {
          extraLarge
        }
        averageScore
        episodes
        status
        genres
        duration
        type
        startDate {
          year
          month
          day
        }
        airingSchedule(perPage: 100) {
          nodes {
            episode
            airingAt
          }
        }
      }
    }
"""


async def _fetch_anilist(variables: dict, query):
    query = query
    max_retries = 3

    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries):
            try:
                async with session.post(
                    "https://graphql.anilist.co",
                    json={"query": query, "variables": variables},
                ) as resp:
                    if resp.status == 429:
                        await asyncio.sleep(2**attempt)
                        continue
                    elif resp.status != 200:
                        return {}
                    return await resp.json()
            except Exception as e:
                logger.warning(f"Request failed: {resp.status} — {variables} — {e}")
                if attempt == max_retries - 1:
                    return {}
                await asyncio.sleep(1)
    return {}


async def get_info_about_anime_from_anilist_by_id(anime_id: int):
    data = await _fetch_anilist({"id": anime_id}, query=_ANILIST_QUERY)
    log_api_response("anilist", data)
    return data


async def get_info_about_anime_from_anilist_by_mal_id(mal_id: int):
    data = await _fetch_anilist({"idMal": mal_id}, query=_ANILIST_QUERY_BY_MAL_ID)
    log_api_response("anilist_mal_id", data)
    return data
