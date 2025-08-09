from database.database import get_db_pool
from loguru import logger


async def upsert_user(telegram_user_id: int, user_language: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (telegram_user_id, user_language)
            VALUES ($1, $2) ON CONFLICT (telegram_user_id) DO
            UPDATE SET
                user_language = EXCLUDED.user_language
            """,
            telegram_user_id,
            user_language,
        )
    logger.info(f"User saved to database {telegram_user_id}")


async def get_user_language_from_db(telegram_user_id: int):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT user_language AS code
            FROM users
            WHERE telegram_user_id = $1
            """,
            telegram_user_id,
        )
    return row["code"] if row else None


async def update_user_language(telegram_user_id: int, language: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.fetchrow(
            """
            UPDATE users
            SET user_language = $1
            WHERE telegram_user_id = $2
            """,
            language,
            telegram_user_id,
        )
    logger.info(f"User {telegram_user_id} change language to {language}")
