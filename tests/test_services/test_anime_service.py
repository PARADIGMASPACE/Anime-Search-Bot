import pytest
from unittest.mock import AsyncMock, patch

from services.anime_service import filter_top_anime, get_caption_and_cover_image

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from services.anime_service import filter_top_anime, get_caption_and_cover_image


class TestFilterTopAnime:
    def test_exact_match_priority(self):
        results = [
            {"id": 1, "name": "Test Anime", "russian": "", "kind": "tv", "score": "7.0", "status": "released"},
            {"id": 2, "name": "Another Test", "russian": "", "kind": "tv", "score": "8.0", "status": "released"},
        ]
        filtered = filter_top_anime(results, "Test Anime", 5)
        assert filtered[0]["id"] == 1

    def test_type_priority_ordering(self):
        results = [
            {"id": 1, "name": "Movie", "russian": "", "kind": "movie", "score": "8.0", "status": "released"},
            {"id": 2, "name": "TV Show", "russian": "", "kind": "tv", "score": "7.0", "status": "released"},
            {"id": 3, "name": "OVA", "russian": "", "kind": "ova", "score": "9.0", "status": "released"},
        ]
        filtered = filter_top_anime(results, "test", 3)
        assert filtered[0]["kind"] == "tv"
        assert filtered[1]["kind"] == "movie"
        assert filtered[2]["kind"] == "ova"

    def test_status_priority_ordering(self):
        results = [
            {"id": 1, "name": "Released", "russian": "", "kind": "tv", "score": "7.0", "status": "released"},
            {"id": 2, "name": "Ongoing", "russian": "", "kind": "tv", "score": "7.0", "status": "ongoing"},
            {"id": 3, "name": "Announced", "russian": "", "kind": "tv", "score": "7.0", "status": "anons"},
        ]
        filtered = filter_top_anime(results, "test", 3)
        assert filtered[0]["status"] == "anons"
        assert filtered[1]["status"] == "ongoing"
        assert filtered[2]["status"] == "released"

    def test_score_ordering(self):
        results = [
            {"id": 1, "name": "Low Score", "russian": "", "kind": "tv", "score": "6.0", "status": "released"},
            {"id": 2, "name": "High Score", "russian": "", "kind": "tv", "score": "9.0", "status": "released"},
            {"id": 3, "name": "Medium Score", "russian": "", "kind": "tv", "score": "7.5", "status": "released"},
        ]
        filtered = filter_top_anime(results, "score", 3)
        assert float(filtered[0]["score"]) >= float(filtered[1]["score"])
        assert float(filtered[1]["score"]) >= float(filtered[2]["score"])

    def test_russian_title_matching(self):
        results = [
            {"id": 1, "name": "English Title", "russian": "Тестовое аниме", "kind": "tv", "score": "7.0",
             "status": "released"},
            {"id": 2, "name": "Another", "russian": "Другое", "kind": "tv", "score": "8.0", "status": "released"},
        ]
        filtered = filter_top_anime(results, "Тестовое аниме", 2)
        assert filtered[0]["id"] == 1

    def test_top_n_limit(self):
        results = [{"id": i, "name": f"Anime {i}", "russian": "", "kind": "tv", "score": "7.0", "status": "released"}
                   for i in range(10)]
        filtered = filter_top_anime(results, "anime", 3)
        assert len(filtered) == 3

    def test_empty_results(self):
        filtered = filter_top_anime([], "test", 5)
        assert filtered == []

    def test_case_insensitive_search(self):
        results = [
            {"id": 1, "name": "UPPERCASE", "russian": "", "kind": "tv", "score": "7.0", "status": "released"},
            {"id": 2, "name": "lowercase", "russian": "", "kind": "tv", "score": "7.0", "status": "released"},
        ]
        filtered = filter_top_anime(results, "uppercase", 2)
        assert any(anime["name"] == "UPPERCASE" for anime in filtered)


class TestGetCaptionAndCoverImage:
    @pytest.mark.asyncio
    async def test_get_with_cached_data(self):
        mock_cached_data = {
            "caption": "Test Caption",
            "cover_image": "test_image.jpg",
            "anilist_id": 123,
            "raw_data_db": {"title": "Test"}
        }

        with patch('services.anime_service.anime_cache.get_cached_anime', new_callable=AsyncMock) as mock_cache:
            mock_cache.return_value = mock_cached_data

            caption, cover_image, anilist_id, raw_data_db = await get_caption_and_cover_image(456, "en")

            assert caption == "Test Caption"
            assert cover_image == "test_image.jpg"
            assert anilist_id == 123
            assert raw_data_db == {"title": "Test"}
            mock_cache.assert_called_once_with(456, "en")

    @pytest.mark.asyncio
    async def test_get_without_cached_data(self):
        mock_shikimori_data = {"myanimelist_id": 789}
        mock_anilist_data = {"data": {"Media": {"id": 123}}}

        with patch('services.anime_service.anime_cache.get_cached_anime', new_callable=AsyncMock) as mock_get_cache, \
                patch('services.anime_service.get_info_about_anime_from_shikimori_by_id',
                      new_callable=AsyncMock) as mock_shiki, \
                patch('services.anime_service.get_info_about_anime_from_anilist_by_mal_id',
                      new_callable=AsyncMock) as mock_anilist, \
                patch('services.anime_service.AnimeInfo') as mock_anime_info, \
                patch('services.anime_service.format_anime_caption', new_callable=AsyncMock) as mock_format, \
                patch('services.anime_service.anime_cache.cache_anime', new_callable=AsyncMock) as mock_cache_set:
            mock_get_cache.return_value = None
            mock_shiki.return_value = mock_shikimori_data
            mock_anilist.return_value = mock_anilist_data
            mock_format.return_value = ("New Caption", "new_image.jpg", {"title": "New"})

            caption, cover_image, anilist_id, raw_data_db = await get_caption_and_cover_image(456, "ru")

            assert caption == "New Caption"
            assert cover_image == "new_image.jpg"
            assert anilist_id == 123
            assert raw_data_db == {"title": "New"}

            mock_shiki.assert_called_once_with(456)
            mock_anilist.assert_called_once_with(789)
            mock_cache_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_with_missing_mal_id(self):
        mock_shikimori_data = {}
        mock_anilist_data = {"data": {"Media": {"id": None}}}

        with patch('services.anime_service.anime_cache.get_cached_anime', new_callable=AsyncMock) as mock_get_cache, \
                patch('services.anime_service.get_info_about_anime_from_shikimori_by_id',
                      new_callable=AsyncMock) as mock_shiki, \
                patch('services.anime_service.get_info_about_anime_from_anilist_by_mal_id',
                      new_callable=AsyncMock) as mock_anilist, \
                patch('services.anime_service.AnimeInfo') as mock_anime_info, \
                patch('services.anime_service.format_anime_caption', new_callable=AsyncMock) as mock_format, \
                patch('services.anime_service.anime_cache.cache_anime', new_callable=AsyncMock) as mock_cache_set:
            mock_get_cache.return_value = None
            mock_shiki.return_value = mock_shikimori_data
            mock_anilist.return_value = mock_anilist_data
            mock_format.return_value = ("Caption", "image.jpg", {})

            caption, cover_image, anilist_id, raw_data_db = await get_caption_and_cover_image(456, "en")

            mock_anilist.assert_called_once_with("")
            assert anilist_id is None

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        with patch('services.anime_service.anime_cache.get_cached_anime', new_callable=AsyncMock) as mock_cache:
            mock_cache.side_effect = Exception("Cache error")

            with pytest.raises(Exception, match="Cache error"):
                await get_caption_and_cover_image(456, "en")

    @pytest.mark.asyncio
    async def test_default_language(self):
        with patch('services.anime_service.anime_cache.get_cached_anime', new_callable=AsyncMock) as mock_cache:
            mock_cache.return_value = {
                "caption": "Test",
                "cover_image": "test.jpg",
                "anilist_id": 123,
                "raw_data_db": {}
            }

            await get_caption_and_cover_image(456, "en")
            mock_cache.assert_called_once_with(456, "en")
