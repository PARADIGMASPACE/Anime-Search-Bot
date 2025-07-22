from api.anilist import get_info_about_anime_from_anilist_by_mal_id
from api.shikimori import get_info_about_anime_from_shikimori_by_id
from common.formating import format_anime_json_info, format_anime_caption


def filter_top_anime(results: list[dict], query: str, top_n: int = 5) -> list[dict]:
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

    def get_relevance(anime):
        name = anime.get('name', '').lower()
        russian = anime.get('russian', '').lower()
        query_lower = query.lower()

        name_score = (
            0 if name == query_lower else
            1 if name.startswith(query_lower) else
            2 if query_lower in name else
            3
        )

        russian_score = (
            0 if russian == query_lower else
            1 if russian.startswith(query_lower) else
            2 if query_lower in russian else
            3
        )

        return min(name_score, russian_score)

    # Отдельно учитываем «часть 1» + «часть 2»
    def get_main_series_key(anime):
        name = anime.get('name', '').lower()
        russian = anime.get('russian', '').lower()
        for postfix in [' 2', ' season 2', ' ii']:
            if name.endswith(postfix):
                return name.replace(postfix, '')
            if russian.endswith(postfix):
                return russian.replace(postfix, '')
        return name or russian

    # Группировка по основной серии
    grouped = {}
    for anime in results:
        key = get_main_series_key(anime)
        grouped.setdefault(key, []).append(anime)

    # Сортировка внутри групп
    sorted_anime = []
    for group in grouped.values():
        group.sort(key=lambda x: (get_relevance(x), get_priority(x), -get_score(x)))
        sorted_anime.extend(group)

    # Финальная сортировка всех
    sorted_anime.sort(key=lambda x: (get_relevance(x), get_priority(x), -get_score(x)))

    return sorted_anime[:top_n]


async def get_caption_and_cover_image(anime_id: int):
    data_from_shikimori = await get_info_about_anime_from_shikimori_by_id(anime_id)
    data_from_anilist = await get_info_about_anime_from_anilist_by_mal_id(data_from_shikimori.get("myanimelist_id", ""))

    formatted_info = format_anime_json_info(data_from_shikimori, data_from_anilist)
    caption, cover_image, anilist_id = await format_anime_caption(formatted_info)

    return caption, cover_image, anilist_id
