import pytest
from unittest.mock import AsyncMock, Mock, patch

from database.anime import upsert_anime, existing_anime, update_anime_episodes


class TestUpsertAnime:
    @pytest.mark.asyncio
    async def test_insert_new_anime(self):
        anime_data = {
            "title_original": "Test Anime",
            "title_ru": "Тестовое аниме",
            "id_anilist": 123,
            "id_shikimori": 456,
            "total_episodes_relase": 24
        }

        mock_row = {"id": 1, "title_original": "Test Anime"}
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row

        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.anime.get_db_pool', return_value=mock_pool), \
             patch('database.anime.logger') as mock_logger:

            result = await upsert_anime(anime_data)

            assert result == 1
            mock_logger.info.assert_called_once_with("Anime saved in database 1 | Test Anime")

    @pytest.mark.asyncio
    async def test_update_existing_anime(self):
        anime_data = {
            "title_original": "Updated Anime",
            "title_ru": "Обновленное аниме",
            "id_anilist": 789,
            "id_shikimori": 456,
            "total_episodes_relase": 12
        }

        mock_row = {"id": 2, "title_original": "Updated Anime"}
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row

        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.anime.get_db_pool', return_value=mock_pool):
            result = await upsert_anime(anime_data)
            assert result == 2

    @pytest.mark.asyncio
    async def test_upsert_with_none_values(self):
        anime_data = {
            "title_original": "Anime with None",
            "title_ru": None,
            "id_anilist": None,
            "id_shikimori": 999,
            "total_episodes_relase": 0
        }

        mock_row = {"id": 3, "title_original": "Anime with None"}
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row

        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.anime.get_db_pool', return_value=mock_pool):
            result = await upsert_anime(anime_data)
            assert result == 3


class TestExistingAnime:
    @pytest.mark.asyncio
    async def test_anime_exists_by_shikimori_id(self):
        mock_row = {"id": 5}
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row

        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.anime.get_db_pool', return_value=mock_pool):
            result = await existing_anime(123, 456)
            assert result == 5

    @pytest.mark.asyncio
    async def test_anime_not_exists(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.anime.get_db_pool', return_value=mock_pool):
            result = await existing_anime(999, 888)
            assert result is False

    @pytest.mark.asyncio
    async def test_existing_anime_with_zero_ids(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.anime.get_db_pool', return_value=mock_pool):
            result = await existing_anime(0, 0)
            assert result is False


class TestUpdateAnimeEpisodes:
    @pytest.mark.asyncio
    async def test_update_episodes_success(self):
        mock_conn = AsyncMock()

        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.anime.get_db_pool', return_value=mock_pool):
            await update_anime_episodes(1, 25)
            mock_conn.execute.assert_called_once_with(
                "UPDATE anime SET total_episodes_relase = $1 WHERE id = $2",
                25,
                1
            )

    @pytest.mark.asyncio
    async def test_update_episodes_zero(self):
        mock_conn = AsyncMock()

        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.anime.get_db_pool', return_value=mock_pool):
            await update_anime_episodes(2, 0)
            mock_conn.execute.assert_called_once_with(
                "UPDATE anime SET total_episodes_relase = $1 WHERE id = $2",
                0,
                2
            )


class TestDatabaseConnection:
    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        with patch('database.anime.get_db_pool', side_effect=Exception("Database connection failed")):
            with pytest.raises(Exception, match="Database connection failed"):
                await upsert_anime({
                    "title_original": "Test",
                    "title_ru": "Тест",
                    "id_anilist": 1,
                    "id_shikimori": 1,
                    "total_episodes_relase": 1
                })

    @pytest.mark.asyncio
    async def test_pool_acquire_error(self):
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.side_effect = Exception("Pool acquire failed")
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.anime.get_db_pool', return_value=mock_pool):
            with pytest.raises(Exception, match="Pool acquire failed"):
                await existing_anime(1, 1)