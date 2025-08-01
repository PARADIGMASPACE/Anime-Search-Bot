import re

from api.anilist import get_info_about_anime_from_anilist_by_mal_id
from api.shikimori import get_info_about_anime_from_shikimori_by_id
from common.anime_caption_formater import format_anime_caption
from common.anime_info_formatter import AnimeInfo


def filter_top_anime(results: list[dict], query: str, top_n: int = 5) -> list[dict]:
    query_lower = query.lower()

    def get_priority(anime):
        anime_type = anime.get('kind') or ''
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

    def normalize(text: str) -> str:
        return re.sub(r'[^a-zа-я0-9]+', ' ', text.lower()).strip()

    def get_relevance(anime):
        name = normalize(anime.get('name', ''))
        russian = normalize(anime.get('russian', ''))
        query_norm = normalize(query)

        name_score = (
            0 if name == query_norm else
            1 if name.startswith(query_norm) else
            2 if query_norm in name else
            3
        )

        russian_score = (
            0 if russian == query_norm else
            1 if russian.startswith(query_norm) else
            2 if query_norm in russian else
            3
        )

        return min(name_score, russian_score)

    exact_matches = [anime for anime in results if anime.get('name', '').lower() == query_lower or anime.get('russian', '').lower() == query_lower]
    other_matches = [anime for anime in results if anime not in exact_matches]
    other_matches.sort(key=lambda x: (get_relevance(x), get_priority(x), -get_score(x)))
    sorted_anime = exact_matches + other_matches
    return sorted_anime[:top_n]


async def get_caption_and_cover_image(shikimori_id: int, lang: str):
    data_from_shikimori = await get_info_about_anime_from_shikimori_by_id(shikimori_id)
    data_from_anilist = await get_info_about_anime_from_anilist_by_mal_id(data_from_shikimori.get("myanimelist_id", ""))
    anilist_id = data_from_anilist.get('data', {}).get('Media', {}).get("id")

    anime_info = AnimeInfo(data_from_shikimori, data_from_anilist)
    caption, cover_image = await format_anime_caption(anime_info, lang=lang)

    return caption, cover_image, anilist_id
