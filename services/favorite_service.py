from api.anilist import get_info_about_anime_from_anilist_by_mal_id
from api.shikimori import get_info_about_anime_from_shikimori_by_id
from utils.utils import classify_airing_schedule


async def formating_data_to_db(shikimori_id, anilist_id):
    data_from_shikimori = await get_info_about_anime_from_shikimori_by_id(shikimori_id)
    mal_id = data_from_shikimori.get("myanimelist_id")

    data_from_anilist = await get_info_about_anime_from_anilist_by_mal_id(mal_id) if mal_id else {}
    data_from_anilist = data_from_anilist.get('data', {}).get('Media', {})

    romaji_name = data_from_shikimori.get("name")
    title_ru = data_from_shikimori.get("russian")
    if not title_ru:
        title_ru = romaji_name
    episodes_count = data_from_anilist.get("episodes") or data_from_shikimori.get("episodes", 0)

    airing_schedule = data_from_anilist.get("airingSchedule", {}).get("nodes", [])
    if airing_schedule:
        classified_schedule = classify_airing_schedule(airing_schedule)
        past_episodes = classified_schedule.get("past", [])
        released_episodes_count = len(past_episodes)
    else:
        released_episodes_count = episodes_count or 0

    anime_data = {
        "title_original": romaji_name,
        "title_ru": title_ru,
        "id_anilist": data_from_anilist.get("id", anilist_id),
        "id_shikimori": shikimori_id,
        "total_episodes_relase": released_episodes_count
    }

    return anime_data