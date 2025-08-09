from datetime import datetime
import html
import re

from loguru import logger


def classify_airing_schedule(schedule: list):
    now = datetime.now().timestamp()
    return {
        "upcoming": [ep for ep in schedule if ep.get("airingAt", 0) > now],
        "past": [ep for ep in schedule if ep.get("airingAt", 0) <= now]
    }

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

    if len_description > 900:
        description = _remove_last_sentences(description, 2)

    max_desc_len = 400 if schedule_text else 500
    if len_description > max_desc_len:
        description = description[:max_desc_len] + "..."
    description = description.replace('<br>', '\n')
    logger.debug(f"<blockquote>{description}</blockquote>")
    return f"<blockquote>{description}</blockquote>"


def format_status(status, data_from_shikimori):
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


def format_type(type_value):
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


def format_genres(genres: list[str]):
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

def get_cover_image(cover_image_data):
    anilist_url = cover_image_data.get("image_anilist")
    shikimori_url = cover_image_data.get("image_shikimori")

    is_anilist_bad = "medium" in anilist_url
    is_shikimori_missing = shikimori_url == "https://shikimori.one/assets/globals/missing_original.jpg"

    if is_anilist_bad and not is_shikimori_missing:
        cover_image = shikimori_url
    else:
        cover_image = anilist_url or (None if is_shikimori_missing else shikimori_url)
    return cover_image