from cache.anime_cache import anime_cache


async def formating_data_to_db(shikimori_id, anilist_id, lang: str = "en"):
    cached_anime = await anime_cache.get_cached_anime(shikimori_id, lang)
    if cached_anime and cached_anime.get("raw_data_db"):
        raw_data_db = cached_anime["raw_data_db"]
        romaji_name = raw_data_db.get("title_original", "")
        title_ru = raw_data_db.get("title_ru", "")
        episodes_count = raw_data_db.get("total_episodes_relase", 0)

        anime_data = {
            "title_original": romaji_name or f"Unknown_{shikimori_id}",
            "title_ru": title_ru,
            "id_anilist": cached_anime.get("anilist_id", anilist_id),
            "id_shikimori": shikimori_id,
            "total_episodes_relase": episodes_count
        }
        return anime_data
    return None