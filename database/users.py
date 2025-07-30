from database.database import get_db_pool

async def upsert_user(telegram_user_id: int, user_language: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (telegram_user_id, user_language)
            VALUES ($1, $2)
            ON CONFLICT (telegram_user_id) DO UPDATE SET
                user_language = EXCLUDED.user_language
            """,
            telegram_user_id, user_language
        )

async def get_user_language_from_db(telegram_user_id: int):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT user_language AS code FROM users WHERE telegram_user_id = $1
            """,
            telegram_user_id
        )
    return row["code"] if row else None


