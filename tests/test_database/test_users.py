import pytest
from unittest.mock import AsyncMock, Mock, patch

from database.users import upsert_user, get_user_language_from_db, update_user_language


class TestUpsertUser:
    @pytest.mark.asyncio
    async def test_insert_new_user(self):
        mock_conn = AsyncMock()
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.users.get_db_pool', return_value=mock_pool), \
             patch('database.users.logger') as mock_logger:

            await upsert_user(123456, "ru")

            mock_conn.execute.assert_called_once_with(
                """
            INSERT INTO users (telegram_user_id, user_language)
            VALUES ($1, $2) ON CONFLICT (telegram_user_id) DO
            UPDATE SET
                user_language = EXCLUDED.user_language
            """,
                123456,
                "ru"
            )
            mock_logger.info.assert_called_once_with("User saved to database 123456")

    @pytest.mark.asyncio
    async def test_update_existing_user(self):
        mock_conn = AsyncMock()
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.users.get_db_pool', return_value=mock_pool), \
             patch('database.users.logger') as mock_logger:

            await upsert_user(789101, "en")

            mock_conn.execute.assert_called_once_with(
                """
            INSERT INTO users (telegram_user_id, user_language)
            VALUES ($1, $2) ON CONFLICT (telegram_user_id) DO
            UPDATE SET
                user_language = EXCLUDED.user_language
            """,
                789101,
                "en"
            )
            mock_logger.info.assert_called_once_with("User saved to database 789101")

    @pytest.mark.asyncio
    async def test_upsert_with_different_languages(self):
        mock_conn = AsyncMock()
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        languages = ["ru", "en"]

        with patch('database.users.get_db_pool', return_value=mock_pool), \
             patch('database.users.logger') as mock_logger:

            for i, lang in enumerate(languages):
                await upsert_user(100 + i, lang)

            assert mock_conn.execute.call_count == 2
            assert mock_logger.info.call_count == 2


class TestGetUserLanguageFromDb:
    @pytest.mark.asyncio
    async def test_get_existing_user_language_ru(self):
        mock_row = {"code": "ru"}
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.users.get_db_pool', return_value=mock_pool):
            result = await get_user_language_from_db(123456)

            assert result == "ru"
            mock_conn.fetchrow.assert_called_once_with(
                """
            SELECT user_language AS code
            FROM users
            WHERE telegram_user_id = $1
            """,
                123456
            )

    @pytest.mark.asyncio
    async def test_get_existing_user_language_en(self):
        mock_row = {"code": "en"}
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.users.get_db_pool', return_value=mock_pool):
            result = await get_user_language_from_db(789101)

            assert result == "en"

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_language(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.users.get_db_pool', return_value=mock_pool):
            result = await get_user_language_from_db(999999)

            assert result is None


class TestUpdateUserLanguage:
    @pytest.mark.asyncio
    async def test_update_language_to_en(self):
        mock_conn = AsyncMock()
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.users.get_db_pool', return_value=mock_pool), \
             patch('database.users.logger') as mock_logger:

            await update_user_language(123456, "en")

            mock_conn.fetchrow.assert_called_once_with(
                """
            UPDATE users
            SET user_language = $1
            WHERE telegram_user_id = $2
            """,
                "en",
                123456
            )
            mock_logger.info.assert_called_once_with("User 123456 change language to en")

    @pytest.mark.asyncio
    async def test_update_language_to_ru(self):
        mock_conn = AsyncMock()
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_conn
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.users.get_db_pool', return_value=mock_pool), \
             patch('database.users.logger') as mock_logger:

            await update_user_language(789101, "ru")

            mock_conn.fetchrow.assert_called_once_with(
                """
            UPDATE users
            SET user_language = $1
            WHERE telegram_user_id = $2
            """,
                "ru",
                789101
            )
            mock_logger.info.assert_called_once_with("User 789101 change language to ru")


class TestDatabaseConnection:
    @pytest.mark.asyncio
    async def test_database_connection_error_upsert(self):
        with patch('database.users.get_db_pool', side_effect=Exception("Database connection failed")):
            with pytest.raises(Exception, match="Database connection failed"):
                await upsert_user(123, "ru")

    @pytest.mark.asyncio
    async def test_database_connection_error_get_language(self):
        with patch('database.users.get_db_pool', side_effect=Exception("Database connection failed")):
            with pytest.raises(Exception, match="Database connection failed"):
                await get_user_language_from_db(123)

    @pytest.mark.asyncio
    async def test_database_connection_error_update_language(self):
        with patch('database.users.get_db_pool', side_effect=Exception("Database connection failed")):
            with pytest.raises(Exception, match="Database connection failed"):
                await update_user_language(123, "en")

    @pytest.mark.asyncio
    async def test_pool_acquire_error(self):
        mock_pool = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.side_effect = Exception("Pool acquire failed")
        mock_context.__aexit__.return_value = None
        mock_pool.acquire.return_value = mock_context

        with patch('database.users.get_db_pool', return_value=mock_pool):
            with pytest.raises(Exception, match="Pool acquire failed"):
                await upsert_user(123, "ru")