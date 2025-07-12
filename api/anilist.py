import aiohttp
from loguru import logger

async def get_data_release_anime(anime_title: str):
    query = '''
query ($search: String) {
  Media(search: $search, type: ANIME) {
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
    '''
    variables = {"search": anime_title}
    async with aiohttp.ClientSession() as session:
        async with session.post("https://graphql.anilist.co", json={"query": query, "variables": variables}) as resp:
            logger.debug(f"{await resp.json()}")
            return await resp.json()

