from loguru import logger
import html
import re
from datetime import datetime


def strip_html_tags(text):
    if not text:
        return ''
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    return text


def remove_last_sentences(text, n=2):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) > n:
        return ' '.join(sentences[:-n])
    return text


async def formating_json(data_from_shikimori, data_from_anilist):
    result = {
        "name": "",
        "description": "",
        "cover_image": "",
        "rating": None,
        "episodes_count": 0,
        "genres": [],
        "type": "",
        "airing_schedule": [],
        "release_date": "",
        "status": ""
    }

    anilist_media = data_from_anilist.get('data', {}).get('Media') or {}

    # Получаем статус из Shikimori или AniList
    shikimori_status = data_from_shikimori.get('status', '').strip()
    anilist_status = anilist_media.get('status', '').strip()

    if shikimori_status:
        result["status"] = shikimori_status
    elif anilist_status:
        anilist_status_map = {
            'FINISHED': 'released',
            'RELEASING': 'ongoing',
            'NOT_YET_RELEASED': 'anons',
            'CANCELLED': 'discontinued',
            'HIATUS': 'paused'
        }
        result["status"] = anilist_status_map.get(anilist_status, anilist_status.lower())
    else:
        result["status"] = ""

    result["name"] = (
            data_from_shikimori.get('title_ru')
            or anilist_media.get('title', {}).get('english')
            or anilist_media.get('title', {}).get('romaji')
            or data_from_shikimori.get('title_en')
            or "Unknown Title"
    )

    description = data_from_shikimori.get('description') or anilist_media.get(
        'description') or "No description available"
    description = strip_html_tags(description)
    description = re.sub(r'\s+', ' ', description).strip()
    result["description"] = description

    # Логика получения обложек
    anilist_cover = anilist_media.get('coverImage', {}).get('extraLarge')
    shikimori_cover = data_from_shikimori.get('image_url')

    logger.debug(f"AniList cover: {anilist_cover}")
    logger.debug(f"Shikimori cover: {shikimori_cover}")

    # Приоритет: Shikimori (если есть) -> AniList -> пустая строка
    if shikimori_cover:
        result["cover_image"] = shikimori_cover
    elif anilist_cover:
        result["cover_image"] = anilist_cover
    else:
        result["cover_image"] = ""

    logger.debug(f"Final cover image URL: {result.get('cover_image', 'No cover')}")



    shikimori_genres = data_from_shikimori.get('genres', [])
    anilist_genres = anilist_media.get('genres', [])

    if shikimori_genres:
        result["genres"] = shikimori_genres
    elif anilist_genres:
        result["genres"] = anilist_genres
    else:
        result["genres"] = []

    # Рейтинг
    anilist_rating = anilist_media.get('averageScore')
    shikimori_score = data_from_shikimori.get('score')

    if anilist_rating:
        result["rating"] = anilist_rating
    elif shikimori_score:
        try:
            score_float = float(shikimori_score)
            result["rating"] = int(score_float * 10)
        except (ValueError, TypeError):
            result["rating"] = None
    else:
        result["rating"] = None

    # Эпизоды
    episodes_anilibria = data_from_shikimori.get('episodes_count')
    episodes_anilist = anilist_media.get('episodes')

    airing_nodes = anilist_media.get('airingSchedule', {}).get('nodes', [])
    max_aired_episode = max((node.get('episode', 0) for node in airing_nodes), default=0)

    if episodes_anilibria and episodes_anilibria > 0:
        result["episodes_count"] = episodes_anilibria
    elif episodes_anilist and episodes_anilist > 0:
        result["episodes_count"] = episodes_anilist
    elif max_aired_episode > 0:
        result["episodes_count"] = max_aired_episode
    else:
        status = result["status"].lower()
        if status in ['ongoing', 'airing', 'анонс', 'выходит', 'releasing']:
            result["episodes_count"] = "?"
        else:
            result["episodes_count"] = 0

    # Дата выхода
    start_date = anilist_media.get('startDate', {})
    if start_date:
        year = start_date.get('year')
        month = start_date.get('month')
        day = start_date.get('day')
        if year and month and day:
            result["release_date"] = f"{year:04d}-{month:02d}-{day:02d}"
        elif year and month:
            result["release_date"] = f"{year:04d}-{month:02d}"
        elif year:
            result["release_date"] = f"{year:04d}"

    result["type"] = (
            data_from_shikimori.get('type')
            or anilist_media.get('type')
            or "Unknown"
    )

    result["airing_schedule"] = [
        {
            "episode": node.get('episode', 0),
            "airing_date": datetime.fromtimestamp(node.get('airingAt', 0)).strftime('%Y-%m-%d %H:%M:%S')
        } for node in airing_nodes
    ]

    return result


def build_anime_caption(result, data_from_shikimori):
    status = result.get('status', '').lower()
    status_display = {
        'anons': 'анонс',
        'ongoing': 'выходит',
        'released': 'завершено',
        'paused': 'приостановлено',
        'discontinued': 'отменено',
        'завершено': 'завершено',
        'выходит': 'выходит',
        'анонс': 'анонс',
        'releasing': 'выходит',
        'not_yet_released': 'анонс',
        'finished': 'завершено',
        'cancelled': 'отменено',
        'hiatus': 'приостановлено'
    }.get(status,
          data_from_shikimori.get('status', status) if data_from_shikimori.get('status') or status else 'неизвестно')

    type_display = {
        'tv': 'Сериал',
        'movie': 'Фильм',
        'ova': 'OVA',
        'ona': 'ONA',
        'special': 'Спешл',
        'music': 'Клип'
    }.get(result['type'].lower() if result['type'] else '', result['type'] or 'Неизвестно')

    rating_text = ""
    if result.get('rating'):
        rating_text = f"<b>⭐️ Рейтинг:</b> {result['rating']}/100\n"

    episodes_text = ""
    if result.get('episodes_count'):
        episodes_text = f"<b>🎮 Эпизодов:</b> {result['episodes_count']}\n"

    date_text = ""
    time_text = ""
    if result['release_date']:
        if len(result['release_date']) == 4:
            date_text = f"<b>🗓 Дата выхода:</b> {result['release_date']}\n"
        elif len(result['release_date']) == 7:
            year, month = result['release_date'].split('-')
            date_text = f"<b>🗓 Дата выхода:</b> {month}.{year}\n"
        elif len(result['release_date']) == 10:
            year, month, day = result['release_date'].split('-')
            date_text = f"<b>🗓 Дата выхода:</b> {day}.{month}.{year}\n"

    if status in ['anons', 'анонс', 'not_yet_released']:
        time_text = "<b>⏰ Время выхода:</b> 00:00\n"

    schedule_text = ""
    if status in ['ongoing', 'выходит', 'releasing'] and result.get('airing_schedule'):
        from datetime import datetime
        current_time = datetime.now()

        upcoming_episodes = []
        for ep in result['airing_schedule']:
            try:
                ep_datetime = datetime.strptime(ep['airing_date'], '%Y-%m-%d %H:%M:%S')
                if ep_datetime > current_time and ep['episode'] > 0:
                    upcoming_episodes.append(ep)
            except ValueError:
                continue

        upcoming_episodes = sorted(upcoming_episodes, key=lambda x: x['airing_date'])[:3]

        if upcoming_episodes:
            schedule_text = "\n<b>📅 Ближайшие серии:</b>\n"
            for ep in upcoming_episodes:
                date_parts = ep['airing_date'].split(' ')
                date_only = date_parts[0] if date_parts else ep['airing_date']
                try:
                    year, month, day = date_only.split('-')
                    formatted_date = f"{day}.{month}.{year}"
                except ValueError:
                    formatted_date = date_only
                schedule_text += f"• Серия {ep['episode']}: {formatted_date}\n"

    header = (
        f"<b>📛 Название:</b> {html.escape(result['name'])}\n"
        f"<b>📺 Тип:</b> {html.escape(type_display)}\n"
        f"<b>ℹ️ Статус:</b> {status_display}\n"
        f"<b>🎭 Жанры:</b> {', '.join(map(html.escape, result['genres']))}\n"
        f"{rating_text}"
        f"{episodes_text}"
        f"{date_text}"
        f"{time_text}"
    )

    if schedule_text:
        header += schedule_text

    description = result['description'] or "Пока нет описания"
    if len(description) > 900:
        description = remove_last_sentences(description, 2)

    max_desc_len = 400 if schedule_text else 500
    if len(description) > max_desc_len:
        description = description[:max_desc_len] + "..."

    formatted_description = f"<blockquote>{html.escape(description)}</blockquote>"

    text = header + formatted_description

    return text