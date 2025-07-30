import html
from datetime import datetime

from api.translate import translate_text
from common.anime_info_formatter import AnimeInfo
from utils.i18n import i18n
from utils.utils import _format_description, get_cover_image, strip_html_tags, format_genres, format_status, format_type


async def format_anime_caption(anime_info: AnimeInfo, lang: str):
    title_data = anime_info.title()
    type_data = anime_info.type()
    status_data = anime_info.status()
    genres_data = anime_info.genres()
    description_data = anime_info.description()
    airing_schedule_data = anime_info.airing_schedule()

    airing_schedule = airing_schedule_data.get("airing_schedule_coming")[:3]

    def format_episodes(episodes):
        res = []
        episode = "Эпизод" if lang == "ru" else "Episode"
        for ep in episodes:
            dt = datetime.fromtimestamp(ep.get('airingAt'))
            res.append(f"{episode} {ep.get('episode')}: {dt.strftime('%Y-%m-%d %H:%M')}")
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
        description = _format_description(description, airing_schedule_str)

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
    episode_count = episode_count_data.get("episode_count_anilist") or episode_count_data.get("episode_count_shikimori")
    release_date = release_date_data.get("release_date_anilist") or release_date_data.get("release_date_shikimori")
    description = _format_description(description, airing_schedule_str)
    cover_image = get_cover_image(cover_image_data)

    caption_parts = []
    if title:
        caption_parts.append(f"<b>{i18n.t('anime.name', lang=lang)}:</b> {title}")

    if type_:
        caption_parts.append(f"<b>{i18n.t('anime.type', lang=lang)}:</b> {type_}")

    if status_:
        caption_parts.append(f"ℹ<b>{i18n.t('anime.status', lang=lang)}:</b> {status_}")

    if genres:
        caption_parts.append(f"<b>{i18n.t('anime.genres', lang=lang)}:</b> {', '.join(map(html.escape, genres))}")

    if rating is not None and rating > 0:
        caption_parts.append(f"<b>{i18n.t('anime.rating', lang=lang)}:</b> {rating}")

    if episode_count is not None and episode_count > 0:
        caption_parts.append(f"<b>{i18n.t('anime.episodes', lang=lang)}:</b> {episode_count}")

    if release_date:
        caption_parts.append(f"<b>{i18n.t('anime.release_date', lang=lang)}:</b> {release_date}")

    if airing_schedule:
        caption_parts.append(f"<b>{i18n.t('anime.upcoming_episodes', lang=lang)}:</b>\n{airing_schedule_str}")

    if description:
        caption_parts.append(description)

    caption = "\n".join(caption_parts)

    return caption, cover_image