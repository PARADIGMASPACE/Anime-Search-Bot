import pytest
from unittest.mock import AsyncMock, Mock, patch

from database.favorites import (
    add_favorite_anime_user,
    get_favorite_anime_user,
    del_favorite_anime_user,
    clear_favorites_user,
    is_favorite_anime_user,
    get_anime_with_users
)


class TestAddFavoriteAnimeUser:
    @pytest.mark.asyncio
    async def test_add_favorite_success(self):
        mock_conn = AsyncMock()
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.favorites.get_db_pool', return_value=mock_pool), \
             patch('database.favorites.logger') as mock_logger:

            await add_favorite_anime_user(123, 456)

            mock_conn.execute.assert_called_once_with(
                """
            INSERT INTO favorites (user_id, anime_id)
            VALUES ($1, $2) ON CONFLICT (user_id, anime_id) DO NOTHING
            """,
                456,
                123
            )
            mock_logger.info.assert_called_once_with("The anime 123 was saved to favorites list for user 456")

    @pytest.mark.asyncio
    async def test_add_favorite_duplicate(self):
        mock_conn = AsyncMock()
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.favorites.get_db_pool', return_value=mock_pool), \
             patch('database.favorites.logger') as mock_logger:

            await add_favorite_anime_user(789, 101112)

            mock_conn.execute.assert_called_once()
            mock_logger.info.assert_called_once()


class TestGetFavoriteAnimeUser:
    @pytest.mark.asyncio
    async def test_get_favorites_with_results(self):
        mock_favorites = [
            {
                "anime_id": 1,
                "anime_title": "Test Anime 1",
                "title_ru": "Тестовое аниме 1",
                "id_shikimori": 100,
                "id_anilist": 200
            },
            {
                "anime_id": 2,
                "anime_title": "Test Anime 2",
                "title_ru": "Тестовое аниме 2",
                "id_shikimori": 101,
                "id_anilist": 201
            }
        ]

        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = mock_favorites
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.favorites.get_db_pool', return_value=mock_pool), \
             patch('database.favorites.logger') as mock_logger:

            result = await get_favorite_anime_user(123)

            assert result == mock_favorites
            mock_logger.info.assert_called_once_with("Retrieved 2 favorites for user 123")

    @pytest.mark.asyncio
    async def test_get_favorites_empty(self):
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.favorites.get_db_pool', return_value=mock_pool), \
             patch('database.favorites.logger') as mock_logger:

            result = await get_favorite_anime_user(999)

            assert result == []
            mock_logger.info.assert_called_once_with("Retrieved 0 favorites for user 999")


class TestDelFavoriteAnimeUser:
    @pytest.mark.asyncio
    async def test_delete_favorite_success(self):
        mock_conn = AsyncMock()
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.favorites.get_db_pool', return_value=mock_pool), \
             patch('database.favorites.logger') as mock_logger:

            await del_favorite_anime_user(123, 456)

            mock_conn.execute.assert_called_once_with(
                "DELETE FROM favorites WHERE anime_id = $1 AND user_id = $2",
                123,
                456
            )
            mock_logger.info.assert_called_once_with("Removed favorite anime_id=123 for user 456")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_favorite(self):
        mock_conn = AsyncMock()
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.favorites.get_db_pool', return_value=mock_pool), \
             patch('database.favorites.logger') as mock_logger:

            await del_favorite_anime_user(999, 888)

            mock_conn.execute.assert_called_once()
            mock_logger.info.assert_called_once()


class TestClearFavoritesUser:
    @pytest.mark.asyncio
    async def test_clear_favorites_success(self):
        mock_conn = AsyncMock()
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.favorites.get_db_pool', return_value=mock_pool), \
             patch('database.favorites.logger') as mock_logger:

            await clear_favorites_user(123)

            mock_conn.execute.assert_called_once_with(
                "DELETE FROM favorites WHERE user_id = $1",
                123
            )
            mock_logger.info.assert_called_once_with("Cleared all favorites for user 123")


class TestIsFavoriteAnimeUser:
    @pytest.mark.asyncio
    async def test_is_favorite_exists(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"1": 1}
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.favorites.get_db_pool', return_value=mock_pool):
            result = await is_favorite_anime_user(123, 456)

            assert result is True
            mock_conn.fetchrow.assert_called_once_with(
                "SELECT 1 FROM favorites WHERE anime_id = $1 AND user_id = $2",
                123,
                456
            )

    @pytest.mark.asyncio
    async def test_is_favorite_not_exists(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.favorites.get_db_pool', return_value=mock_pool):
            result = await is_favorite_anime_user(999, 888)

            assert result is False


class TestGetAnimeWithUsers:
    @pytest.mark.asyncio
    async def test_get_anime_with_users_success(self):
        mock_rows = [
            {
                "id": 1,
                "id_anilist": 100,
                "id_shikimori": 200,
                "title_original": "Test Anime 1",
                "title_ru": "Тестовое аниме 1",
                "total_episodes_relase": 12,
                "user_ids": [101, 102],
                "user_languages": ["ru", "en"]
            },
            {
                "id": 2,
                "id_anilist": 101,
                "id_shikimori": 201,
                "title_original": "Test Anime 2",
                "title_ru": "Тестовое аниме 2",
                "total_episodes_relase": 24,
                "user_ids": [103],
                "user_languages": ["ru"]
            }
        ]

        expected_result = {
            1: {
                "id_anilist": 100,
                "id_shikimori": 200,
                "title_original": "Test Anime 1",
                "title_ru": "Тестовое аниме 1",
                "current_episodes": 12,
                "user_ids": [101, 102],
                "user_languages": ["ru", "en"]
            },
            2: {
                "id_anilist": 101,
                "id_shikimori": 201,
                "title_original": "Test Anime 2",
                "title_ru": "Тестовое аниме 2",
                "current_episodes": 24,
                "user_ids": [103],
                "user_languages": ["ru"]
            }
        }

        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = mock_rows
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.favorites.get_db_pool', return_value=mock_pool), \
             patch('database.favorites.logger') as mock_logger:

            result = await get_anime_with_users()

            assert result == expected_result
            mock_logger.info.assert_called_once_with("Retrieved 2 anime with associated users")

    @pytest.mark.asyncio
    async def test_get_anime_with_users_empty(self):
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.favorites.get_db_pool', return_value=mock_pool), \
             patch('database.favorites.logger') as mock_logger:

            result = await get_anime_with_users()

            assert result == {}
            mock_logger.info.assert_called_once_with("Retrieved 0 anime with associated users")


class TestDatabaseConnection:
    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        with patch('database.favorites.get_db_pool', side_effect=Exception("Database connection failed")):
            with pytest.raises(Exception, match="Database connection failed"):
                await add_favorite_anime_user(1, 1)

    @pytest.mark.asyncio
    async def test_pool_acquire_error(self):
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.side_effect = Exception("Pool acquire failed")
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.favorites.get_db_pool', return_value=mock_pool):
            with pytest.raises(Exception, match="Pool acquire failed"):
                await is_favorite_anime_user(1, 1)