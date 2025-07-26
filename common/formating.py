from loguru import logger
import html
import re
from datetime import datetime
from api.translate import translate_text
from utils.i18n import i18n

def _get_id(data_from_shikimori, data_from_anilist):
    result_id = {
        "shikimori_id": data_from_shikimori.get("id", ""),
        "anilist_id": data_from_anilist.get("id", "")
    }

    return result_id


def _get_title(data_from_shikimori, data_from_anilist):
    result_name = {
        "native": data_from_anilist.get("title", {}).get("native", ""),
        "romaji": data_from_anilist.get("title", {}).get("romaji", ""),
        "english": data_from_shikimori.get("name", ""),
        "russian": data_from_shikimori.get("russian", "")
    }
    return result_name


def _get_description(data_from_shikimori, data_from_anilist):
    result_description = {
        "desc_shikimori": data_from_shikimori.get("description", ""),
        "desc_anilist": data_from_anilist.get("description", ""),
    }
    return result_description


def _get_cover_image(data_from_shikimori, data_from_anilist):
    result_cover_image = {
        "image_shikimori": "https://shikimori.one" + data_from_shikimori.get("image", {}).get("original", ""),
        "image_anilist": data_from_anilist.get("coverImage", {}).get("extraLarge", ""),
    }

    return result_cover_image


def _get_genres(data_from_shikimori, data_from_anilist):
    genres_anilist = data_from_anilist.get("genres", [])

    genres_shikimori_raw = data_from_shikimori.get("genres", [])
    genres_shikimori = [g.get("russian", g.get("name", "")) for g in genres_shikimori_raw]

    result_genres = {
        "genres_shikimori": genres_shikimori,
        "genres_anilist": genres_anilist,
    }

    return result_genres


def _get_rating(data_from_shikimori, data_from_anilist):
    rating_shikimori = float(data_from_shikimori.get("score", 0)) * 10

    result_rating = {
        "rating_shikimori": rating_shikimori,
        "rating_anilist": data_from_anilist.get("averageScore", 0),
    }

    return result_rating


def _get_episode_count(data_from_shikimori, data_from_anilist):
    result_episode_count = {
        "episode_count_shikimori": data_from_shikimori.get("episodes", 0),
        "episode_count_anilist": data_from_anilist.get("episodes", 0),
    }

    return result_episode_count


def _get_release_date(data_from_shikimori, data_from_anilist):
    release_date_anilist_data = data_from_anilist.get("startDate", {})

    try:
        y, m, d = release_date_anilist_data.get('year'), release_date_anilist_data.get(
            'month'), release_date_anilist_data.get('day')
        if y and m and d:
            release_date_anilist = f"{y:04d}-{m:02d}-{d:02d}"
        elif y and m:
            release_date_anilist = f"{y:04d}-{m:02d}"
        elif y:
            release_date_anilist = f"{y:04d}"
        release_date_anilist = ""
    except Exception as e:
        logger.error(f"Error formatting release date from Anilist: {e}")
        release_date_anilist = ""

    result_release_date = {
        "release_date_shikimori": data_from_shikimori.get("aired_on", ""),
        "release_data_anilist": release_date_anilist,
    }

    return result_release_date


def classify_airing_schedule(schedule: list):
    now = datetime.now().timestamp()
    return {
        "upcoming": [ep for ep in schedule if ep.get("airingAt", 0) > now],
        "past": [ep for ep in schedule if ep.get("airingAt", 0) <= now]
    }


def _get_airing_schedule(data_from_shikimori, data_from_anilist):
    airing_schedule_shikimori = data_from_shikimori.get("episodes", [])

    airing_schedule_anilist = data_from_anilist.get("airingSchedule", {}).get("nodes", [])

    airing_schedule_classified = classify_airing_schedule(airing_schedule_anilist)
    airing_schedule_coming = airing_schedule_classified.get("upcoming", [])

    result_airing_schedule = {
        "airing_schedule_shikimori": airing_schedule_shikimori,
        "airing_schedule_anilist": airing_schedule_anilist,
        "airing_schedule_coming": airing_schedule_coming
    }

    return result_airing_schedule


def _get_type(data_from_shikimori, data_from_anilist):
    result_type = {
        "type_shikimori": data_from_shikimori.get("kind", ""),
        "type_anilist": data_from_anilist.get("type", ""),
    }

    return result_type


def _get_status(data_from_shikimori, data_from_anilist):
    result_status = {
        "status_shikimori": data_from_shikimori.get("status", ""),
        "status_anilist": data_from_anilist.get("status", ""),
    }
    return result_status


def strip_html_tags(text):
    if not text:
        return ''

    text = html.unescape(text)
    text = re.sub(r'<[^>]*?>', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def _remove_last_sentences(text, n=2):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) > n:
        return ' '.join(sentences[:-n])
    return text


def _format_description(description, schedule_text):
    if description is None:
        return None

    len_description = len(description)

    if len_description < 200:
        return None

    if len_description > 900:
        description = _remove_last_sentences(description, 2)

    max_desc_len = 400 if schedule_text else 500
    if len_description > max_desc_len:
        description = description[:max_desc_len] + "..."

    return f"<blockquote>{description}</blockquote>"


def _format_status(status, data_from_shikimori):
    status_lower = status.lower()
    status_display = {
        'anons': 'Анонс',
        'ongoing': 'Выходит',
        'released': 'Завершено',
        'paused': 'Приостановлено',
        'discontinued': 'Отменено',
        'завершено': 'Завершено',
        'выходит': 'Выходит',
        'анонс': 'Анонс',
        'releasing': 'Выходит',
        'not_yet_released': 'Анонс',
        'finished': 'Завершено',
        'cancelled': 'Отменено',
        'hiatus': 'Приостановлено'
    }

    return status_display.get(
        status_lower,
        data_from_shikimori.get('status', status) if data_from_shikimori.get('status') or status else 'неизвестно'
    )


def _format_type(type_value):
    type_lower = (type_value or '').lower()
    type_display = {
        'tv': 'TV-сериал',
        'movie': 'Фильм',
        'ova': 'OVA',
        'ona': 'ONA',
        'special': 'Спешл',
        'music': 'Клип',
        'tv_special': 'ТВ-спешл',
        'тв-сериал': 'TV-сериал',
        'фильм': 'Фильм',
        'спешл': 'Спешл',
        'она': 'ONA',
        'ова': 'OVA',
        'клип': 'Клип'
    }

    return type_display.get(type_lower, 'Неизвестно')


def _format_genres(genres: list[str]):
    genre_mapping = {
        'action': 'Экшен',
        'adventure': 'Приключения',
        'comedy': 'Комедия',
        'drama': 'Драма',
        'fantasy': 'Фэнтези',
        'sci-fi': 'Научная фантастика',
        'romance': 'Романтика',
        'mystery': 'Мистика',
        'horror': 'Ужасы',
        'slice of life': 'Повседневность',
        'sports': 'Спорт',
        'supernatural': 'Сверхъестественное',
        'psychological': 'Психология',
        'thriller': 'Триллер',
        'ecchi': 'Этти',
        'mecha': 'Меха',
        'isekai': 'Исекай',
        'school': 'Школа',
        'music': 'Музыка',
        'military': 'Военное',
        'game': 'Игры',
        'demons': 'Демоны',
        'historical': 'История',
        'magic': 'Магия',
        'parody': 'Пародия',
        'yaoi': 'Яой',
        'yuri': 'Юри',
        'harem': 'Гарем',
        'shounen': 'Сёнэн',
        'shoujo': 'Сёдзё',
        'josei': 'Дзёсэй',
        'seinen': 'Сэйнэн',
        'doujinshi': 'Додзинси'
    }

    translated = [genre_mapping.get(g.lower(), g) for g in genres]
    return translated


def format_anime_json_info(data_from_shikimori, data_from_anilist):
    data_from_anilist = data_from_anilist.get('data', {}).get('Media', {})
    id = _get_id(data_from_shikimori, data_from_anilist)
    title = _get_title(data_from_shikimori, data_from_anilist)
    description = _get_description(data_from_shikimori, data_from_anilist)
    cover_image = _get_cover_image(data_from_shikimori, data_from_anilist)
    genres = _get_genres(data_from_shikimori, data_from_anilist)
    rating = _get_rating(data_from_shikimori, data_from_anilist)
    episode_count = _get_episode_count(data_from_shikimori, data_from_anilist)
    release_date = _get_release_date(data_from_shikimori, data_from_anilist)
    airing_schedule = _get_airing_schedule(data_from_shikimori, data_from_anilist)
    type_info = _get_type(data_from_shikimori, data_from_anilist)
    status = _get_status(data_from_shikimori, data_from_anilist)

    result = {
        "id": id,
        "title": title,
        "description": description,
        "cover_image": cover_image,
        "genres": genres,
        "rating": rating,
        "episode_count": episode_count,
        "release_date": release_date,
        "airing_schedule": airing_schedule,
        "type_info": type_info,
        "status": status
    }
    logger.debug(result)
    return result


async def format_anime_caption(json_with_anime_info, lang: str = None):
    anilist_id_raw = json_with_anime_info.get("id", {}).get("anilist_id")
    try:
        anilist_id = int(anilist_id_raw) if anilist_id_raw not in (None, "") else None
    except (ValueError, TypeError):
        anilist_id = None

    title = json_with_anime_info.get("title").get("russian") or json_with_anime_info.get("title").get(
        "english") or json_with_anime_info.get("title").get("romaji")

    genres = json_with_anime_info.get("genres").get("genres_shikimori") or json_with_anime_info.get("genres").get(
        "genres_anilist")
    genres = _format_genres(genres)

    rating = json_with_anime_info.get("rating").get("rating_shikimori") or json_with_anime_info.get("rating").get(
        "rating_anilist")
    if rating is None:
        rating = 0
    else:
        rating = round(rating, 2)

    release_date = json_with_anime_info.get("release_date").get("release_date_shikimori") or json_with_anime_info.get(
        "release_date").get("release_data_anilist")

    episode_count = json_with_anime_info.get("episode_count").get("episode_count_anilist") or json_with_anime_info.get(
        "episode_count").get("episode_count_shikimori")

    airing_schedule = json_with_anime_info.get("airing_schedule", {}).get("airing_schedule_coming", [])

    def format_episode(ep):
        dt = datetime.fromtimestamp(ep.get('airingAt'))
        day_key = f"anime.days.{dt.strftime('%A').lower()}"
        month_key = f"anime.months.{dt.strftime('%B').lower()}"
        month_year = dt.strftime('%Y') + ' ' + i18n.t(month_key, lang=lang)
        time = dt.strftime('%H:%M')
        return i18n.t("anime.episode", lang=lang, number=ep.get('episode'), month_year=month_year, day=i18n.t(day_key, lang=lang), time=time)

    airing_schedule_str = "\n".join([format_episode(ep) for ep in airing_schedule[:3]])

    desc_shikimori = json_with_anime_info.get("description").get("desc_shikimori")
    description = desc_shikimori

    if not description:
        desc_anilist = json_with_anime_info.get("description").get("desc_anilist")
        if desc_anilist:
            description = await translate_text(desc_anilist)
        else:
            description = None
    description = strip_html_tags(description)

    if not description or len(description) < 200:
        description = None

    formatted_description = _format_description(description, airing_schedule_str)

    type_info = json_with_anime_info.get("type_info").get("type_shikimori") or json_with_anime_info.get(
        "type_info").get("type_anilist")

    status = json_with_anime_info.get("status").get("status_shikimori") or json_with_anime_info.get("status").get(
        "status_anilist")
    cover_image = json_with_anime_info.get("cover_image").get("image_anilist") or json_with_anime_info.get("cover_image").get("image_shikimori")

    caption_parts = []
    if title:
        caption_parts.append(f"<b>{i18n.t('anime.name', lang=lang)}:</b> {title}")

    if type_info:
        type_info = _format_type(type_info)
        caption_parts.append(f"<b>{i18n.t('anime.type', lang=lang)}:</b> {type_info}")

    if status:
        formatted_status = _format_status(status, json_with_anime_info.get("status"))
        caption_parts.append(f"ℹ<b>{i18n.t('anime.status', lang=lang)}:</b> {formatted_status}")

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

    if formatted_description:
        caption_parts.append(formatted_description)

    caption = "\n".join(caption_parts)

    return caption, cover_image, anilist_id