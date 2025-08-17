import html
from datetime import datetime

from loguru import logger

from api.translate import translate_text
from common.anime_info_formatter import AnimeInfo
from utils.i18n import i18n
from utils.utils import (
    _format_description,
    get_cover_image,
    strip_html_tags,
    format_genres,
    format_status,
    format_type,
    log_api_response,
)
from utils.utils import classify_airing_schedule


async def format_anime_caption(anime_info: AnimeInfo, lang: str):
    log_api_response("anime_info_input", anime_info.__dict__)

    title_data = anime_info.title()
    type_data = anime_info.type()
    status_data = anime_info.status()
    genres_data = anime_info.genres()
    description_data = anime_info.description()
    airing_schedule_data = anime_info.airing_schedule()

    airing_schedule = airing_schedule_data.get("airing_schedule_coming")[:3]
    airing_schedule_classified = airing_schedule_data.get("airing_schedule_anilist", [])
    classified_schedule = classify_airing_schedule(airing_schedule_classified)
    aired_episodes_count = len(classified_schedule.get("past", []))

    episode_count_data = anime_info.episode_count()
    total_episodes = episode_count_data.get("episode_count_anilist") or episode_count_data.get("episode_count_shikimori")
    status_data = anime_info.status()

    if aired_episodes_count == 0 and total_episodes and total_episodes > 0:
        status_anilist = status_data.get("status_anilist", "").upper()
        status_shikimori = status_data.get("status_shikimori", "").lower()

        is_finished = (
            status_anilist in ["FINISHED", "COMPLETED"] or
            status_shikimori in ["released", "завершено"]
        )

        if is_finished:
            aired_episodes_count = total_episodes

    def format_episodes(episodes):
        res = []
        episode = "Эпизод" if lang == "ru" else "Episode"
        for ep in episodes:
            dt = datetime.fromtimestamp(ep.get("airingAt"))
            res.append(
                f"{episode} {ep.get('episode')}: {dt.strftime('%Y-%m-%d %H:%M')}"
            )
        return "\n".join(res)

    airing_schedule_str = format_episodes(airing_schedule)

    if lang == "ru":
        title = title_data.get("russian")

        type_ = type_data.get("type_shikimori")
        type_ = format_type(type_)

        status_ = status_data.get("status_shikimori")
        status_ = format_status(status_, status_data)

        genres = genres_data.get("genres_shikimori")
        genres = format_genres(genres)

        description = description_data.get("desc_shikimori")
        description = strip_html_tags(description)

        if not description:
            description = description_data.get("desc_anilist")
            description = strip_html_tags(description)
            description = await translate_text(description)

    else:
        title = title_data.get("romaji")
        type_ = type_data.get("type_anilist")
        status_ = status_data.get("status_anilist")
        genres = genres_data.get("genres_anilist")
        description = description_data.get("desc_anilist")
        description = strip_html_tags(description)

    rating_data = anime_info.rating()
    episode_count_data = anime_info.episode_count()
    release_date_data = anime_info.release_date()
    cover_image_data = anime_info.cover_image()

    rating = rating_data.get("rating_anilist") or rating_data.get("rating_shikimori")
    episode_count = episode_count_data.get(
        "episode_count_anilist"
    ) or episode_count_data.get("episode_count_shikimori")
    release_date = release_date_data.get(
        "release_date_anilist"
    ) or release_date_data.get("release_date_shikimori")
    description = _format_description(description, airing_schedule_str)
    cover_image = get_cover_image(cover_image_data)

    raw_data_db = {
        "total_episodes_relase": aired_episodes_count,
        "title_ru": title_data.get("russian") or "",
        "title_original": title_data.get("romaji")
        or title_data.get("english")
        or f"Unknown_{anime_info.ids.get('shikimori_id', 0)}",
        "airing_schedule_count": aired_episodes_count
    }
    logger.info(raw_data_db)
    caption_parts = []
    if title:
        caption_parts.append(f"<b>{i18n.t('anime.name', lang=lang)}:</b> {title}")

    if type_:
        caption_parts.append(f"<b>{i18n.t('anime.type', lang=lang)}:</b> {type_}")

    if status_:
        caption_parts.append(f"ℹ<b>{i18n.t('anime.status', lang=lang)}:</b> {status_}")

    if genres:
        caption_parts.append(
            f"<b>{i18n.t('anime.genres', lang=lang)}:</b> {', '.join(map(html.escape, genres))}"
        )

    if rating is not None and rating > 0:
        caption_parts.append(f"<b>{i18n.t('anime.rating', lang=lang)}:</b> {rating}")

    if episode_count is not None and episode_count > 0:
        caption_parts.append(
            f"<b>{i18n.t('anime.episodes', lang=lang)}:</b> {episode_count}"
        )

    if release_date:
        caption_parts.append(
            f"<b>{i18n.t('anime.release_date', lang=lang)}:</b> {release_date}"
        )

    if airing_schedule:
        caption_parts.append(
            f"<b>{i18n.t('anime.upcoming_episodes', lang=lang)}:</b>\n{airing_schedule_str}"
        )

    if description:
        caption_parts.append(description)

    caption = "\n".join(caption_parts)
    debug_info = {
        "title": title,
        "type": type_,
        "status": status_,
        "genres": genres,
        "rating": rating,
        "episode_count": episode_count,
        "release_date": release_date,
        "airing_schedule": airing_schedule_str,
        "description": description,
        "cover_image": cover_image,
        "raw_data_db": raw_data_db,
        "anime_info_ids": getattr(anime_info, "ids", {}),
    }
    log_api_response("caption_debug", debug_info)
    return caption, cover_image, raw_data_db
