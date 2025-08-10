import pytest
from datetime import datetime
import tempfile
import os
import json
from unittest.mock import patch, mock_open

from utils.utils import (
    classify_airing_schedule,
    strip_html_tags,
    _remove_last_sentences,
    _format_description,
    format_status,
    format_type,
    format_genres,
    get_cover_image,
    log_api_response
)


class TestClassifyAiringSchedule:
    def test_classify_empty_schedule(self):
        result = classify_airing_schedule([])
        assert result == {"upcoming": [], "past": []}

    def test_classify_mixed_schedule(self):
        now = datetime.now().timestamp()
        schedule = [
            {"airingAt": now + 3600},
            {"airingAt": now - 3600},
            {"airingAt": now + 7200},
        ]
        result = classify_airing_schedule(schedule)
        assert len(result["upcoming"]) == 2
        assert len(result["past"]) == 1


class TestStripHtmlTags:
    def test_strip_empty_text(self):
        assert strip_html_tags("") == ""
        assert strip_html_tags(None) == ""

    def test_strip_html_tags(self):
        text = "<p>one <b>two</b></p>"
        result = strip_html_tags(text)
        assert result == "one two"

    def test_strip_markdown_formatting(self):
        text = "**hello** __none__ *three*"
        result = strip_html_tags(text)
        assert result == "hello none three"

    def test_strip_brackets(self):
        text = "text [from] site"
        result = strip_html_tags(text)
        assert result == "text site"


class TestRemoveLastSentences:
    def test_remove_from_multiple_sentences(self):
        text = "apple. yellow. table. gift."
        result = _remove_last_sentences(text, 2)
        assert result == "apple. yellow."

    def test_remove_from_few_sentences(self):
        text = "apple."
        result = _remove_last_sentences(text, 2)
        assert result == "apple."

class TestFormatDescription:
    def test_format_none_description(self):
        result = _format_description(None, "")
        assert result is None

    def test_format_short_description(self):
        desc = "Short desc"
        result = _format_description(desc, "")
        assert result == "<blockquote>Short desc</blockquote>"

    def test_format_long_description_with_schedule(self):
        desc = "а" * 500
        result = _format_description(desc, "schedule")
        assert "..." in result
        assert result.startswith("<blockquote>")


class TestFormatStatus:
    def test_format_known_status(self):
        assert format_status("ongoing", {}) == "Выходит"
        assert format_status("released", {}) == "Завершено"
        assert format_status("анонс", {}) == "Анонс"

    def test_format_unknown_status_with_fallback(self):
        data = {"status": "custom_status"}
        result = format_status("unknown", data)
        assert result == "custom_status"


class TestFormatType:
    def test_format_known_types(self):
        assert format_type("tv") == "TV-сериал"
        assert format_type("movie") == "Фильм"
        assert format_type("OVA") == "OVA"

    def test_format_unknown_type(self):
        assert format_type("unknown") == "Неизвестно"
        assert format_type(None) == "Неизвестно"


class TestFormatGenres:
    def test_format_known_genres(self):
        genres = ["action", "comedy", "drama"]
        result = format_genres(genres)
        assert result == ["Экшен", "Комедия", "Драма"]

    def test_format_mixed_genres(self):
        genres = ["action", "unknown_genre"]
        result = format_genres(genres)
        assert result == ["Экшен", "unknown_genre"]


class TestGetCoverImage:
    def test_prefer_shikimori_when_anilist_bad(self):
        data = {
            "image_anilist": "https://s4.anilist.co/file/anilistcdn/media/anime/cover/medium/1.jpg",
            "image_shikimori": "https://shikimori.one/good_image.jpg"
        }
        result = get_cover_image(data)
        assert result == "https://shikimori.one/good_image.jpg"

    def test_use_anilist_when_good(self):
        data = {
            "image_anilist": "https://s4.anilist.co/file/anilistcdn/media/anime/cover/large/1.jpg",
            "image_shikimori": "https://shikimori.one/assets/globals/missing_original.jpg"
        }
        result = get_cover_image(data)
        assert result == "https://s4.anilist.co/file/anilistcdn/media/anime/cover/large/1.jpg"

