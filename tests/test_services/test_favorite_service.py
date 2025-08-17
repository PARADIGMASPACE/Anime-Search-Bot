import pytest
from unittest.mock import AsyncMock, patch

from services.favorite_service import formating_data_to_db


class TestFormatingDataToDb:
    @pytest.mark.asyncio
    async def test_format_with_cached_data(self):
        mock_cached_anime = {
            "anilist_id": 123,
            "raw_data_db": {
                "title_original": "Test Anime",
                "title_ru": "Тестовое Аниме",
                "airing_schedule_count": 24
            }
        }

        with patch('services.favorite_service.anime_cache.get_cached_anime',
                   new_callable=AsyncMock) as mock_get_cache:
            mock_get_cache.return_value = mock_cached_anime

            result = await formating_data_to_db(456, 123, "ru")

            expected = {
                "title_original": "Test Anime",
                "title_ru": "Тестовое Аниме",
                "id_anilist": 123,
                "id_shikimori": 456,
                "total_episodes_relase": 24
            }

            assert result == expected
            mock_get_cache.assert_called_once_with(456, "ru")

    @pytest.mark.asyncio
    async def test_format_with_partial_data(self):
        mock_cached_anime = {
            "anilist_id": 789,
            "raw_data_db": {
                "title_original": "",
                "title_ru": "Русское название",
                "airing_schedule_count": 0
            }
        }

        with patch('services.favorite_service.anime_cache.get_cached_anime',
                   new_callable=AsyncMock) as mock_get_cache:
            mock_get_cache.return_value = mock_cached_anime

            result = await formating_data_to_db(999, 789)

            expected = {
                "title_original": "Unknown_999",
                "title_ru": "Русское название",
                "id_anilist": 789,
                "id_shikimori": 999,
                "total_episodes_relase": 0
            }

            assert result == expected

    @pytest.mark.asyncio
    async def test_format_no_cached_data(self):
        with patch('services.favorite_service.anime_cache.get_cached_anime',
                   new_callable=AsyncMock) as mock_get_cache:
            mock_get_cache.return_value = None

            result = await formating_data_to_db(123, 456)

            assert result is None
            mock_get_cache.assert_called_once_with(123, "en")

    @pytest.mark.asyncio
    async def test_format_cached_without_raw_data(self):
        mock_cached_anime = {
            "anilist_id": 111,
        }

        with patch('services.favorite_service.anime_cache.get_cached_anime',
                   new_callable=AsyncMock) as mock_get_cache:
            mock_get_cache.return_value = mock_cached_anime

            result = await formating_data_to_db(222, 111)

            assert result is None

    @pytest.mark.asyncio
    async def test_format_missing_anilist_id_uses_fallback(self):
        mock_cached_anime = {
            "raw_data_db": {
                "title_original": "Fallback Test",
                "title_ru": "",
                "airing_schedule_count": 12
            }
        }

        with patch('services.favorite_service.anime_cache.get_cached_anime',
                   new_callable=AsyncMock) as mock_get_cache:
            mock_get_cache.return_value = mock_cached_anime

            result = await formating_data_to_db(333, 777)

            expected = {
                "title_original": "Fallback Test",
                "title_ru": "",
                "id_anilist": 777,
                "id_shikimori": 333,
                "total_episodes_relase": 12
            }

            assert result == expected

    @pytest.mark.asyncio
    async def test_default_language_parameter(self):
        with patch('services.favorite_service.anime_cache.get_cached_anime',
                   new_callable=AsyncMock) as mock_get_cache:
            mock_get_cache.return_value = None

            await formating_data_to_db(100, 200)

            mock_get_cache.assert_called_once_with(100, "en")