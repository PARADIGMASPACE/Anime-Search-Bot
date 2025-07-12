
import aiohttp
import asyncio
from loguru import logger

async def search_anime_id(name_of_russian):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://shikimori.one/api/animes?search={name_of_russian}") as resp:
                    if resp.status == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return await resp.json()
        except Exception:
            if attempt == max_retries - 1:
                return []
            await asyncio.sleep(1)
    return []


async def get_info_from_shikimori(anime_id):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://shikimori.one/api/animes/{anime_id}") as resp:
                    if resp.status == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return await resp.json()
        except Exception:
            if attempt == max_retries - 1:
                return {}
            await asyncio.sleep(1)
    return {}


async def get_anime_by_id_shikimori(anime_id):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://shikimori.one/api/animes/{anime_id}") as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
    except Exception:
        return None


async def search_multiple_anime(query: str):
    results = []

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://shikimori.one/api/animes?search={query}&limit=20") as resp:
            if resp.status == 200:
                shikimori_results = await resp.json()
                for anime in shikimori_results:
                    # Правильно обрабатываем картинку здесь
                    cover_image = ""
                    if anime.get('image'):
                        original_path = anime['image']['original']
                        if original_path != "/assets/globals/missing_original.jpg":
                            cover_image = f"https://shikimori.one{original_path}"

                    results.append({
                        'id': anime.get('id'),
                        'name': anime.get('russian') or anime.get('name'),
                        'type': anime.get('kind'),
                        'status': anime.get('status'),
                        'episodes': anime.get('episodes'),
                        'score': anime.get('score'),
                        'cover_image': cover_image  # Используем обработанную картинку
                    })

    # Остальной код сортировки остается без изменений
    def get_priority(anime):
        anime_type = anime.get('type') or ''
        anime_status = anime.get('status', '').lower()

        type_priority = {
            'tv': 1,
            'movie': 2,
            'ova': 3,
            'ona': 3,
            'special': 3,
            'music': 4
        }

        status_priority = {
            'anons': 1,
            'announced': 1,
            'ongoing': 2,
            'выходит': 2,
            'released': 3,
            'завершено': 3,
            'paused': 4,
            'discontinued': 5
        }

        type_val = type_priority.get(anime_type.lower(), 5)
        status_val = status_priority.get(anime_status, 6)

        return (type_val, status_val)

    def get_score(anime):
        score = anime.get('score') or 0
        try:
            return float(score)
        except (ValueError, TypeError):
            return 0.0

    def get_relevance(anime, query):
        name = anime.get('name', '').lower()
        query_lower = query.lower()

        if name == query_lower:
            return 0
        elif name.startswith(query_lower):
            return 1
        elif query_lower in name:
            return 2
        else:
            return 3

    results.sort(key=lambda x: (get_relevance(x, query), get_priority(x), -get_score(x)))

    return results[:5]

async def take_id_from_shikimori(anime_name):
    anime_data = await search_anime_id(anime_name)
    if not anime_data:
        return None
    return anime_data[0].get('id')


async def json_with_anime_info_shikimori(anime_name):
    anime_id = await take_id_from_shikimori(anime_name)
    if anime_id is None:
        return {
            "anime_id": None,
            "title_ru": None,
            "title_en": anime_name,
            "status": "",
            "image_url": "",
            "type": "",
            "episodes_count": 0,
            "episode_duration_min": 0,
            "genres": [],
            "description": "",
            "in_favorites": 0,
            "score": None
        }

    anime_info = await get_info_from_shikimori(anime_id)
    if not anime_info:
        return {"anime_id": None}

    genres = []
    if anime_info.get('genres'):
        genres = [genre.get('russian') for genre in anime_info['genres'] if genre.get('russian')]

    # Формируем URL картинки из Shikimori
    image_url = ""
    if anime_info.get('image'):
        original_path = anime_info['image']['original']

        if original_path == "/assets/globals/missing_original.jpg":
            image_url = ""
        else:
            image_url = f"https://shikimori.one{original_path}"

    result = {
        "anime_id": anime_info.get('id'),
        "title_ru": anime_info.get('russian'),
        "title_en": anime_info.get('name'),
        "status": anime_info.get('status'),
        "image_url": image_url,
        "type": anime_info.get('kind'),
        "episodes_count": anime_info.get('episodes') or 0,
        "episode_duration_min": anime_info.get('duration', 0),
        "genres": genres,
        "description": anime_info.get('description', ""),
        "in_favorites": anime_info.get('in_favorites', 0),
        "score": anime_info.get('score')
    }

    return result