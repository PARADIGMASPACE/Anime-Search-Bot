from database.database import get_db_pool

async def upsert_user(telegram_user_id: int, user_language: str = 'en', preferred_language_id: int = None):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (telegram_user_id, user_language, preferred_language_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (telegram_user_id) DO UPDATE SET
                user_language = EXCLUDED.user_language,
                preferred_language_id = EXCLUDED.preferred_language_id
            """,
            telegram_user_id, user_language, preferred_language_id
        )


async def get_user_language(telegram_user_id: int):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT l.code
            FROM users u
            LEFT JOIN languages l ON u.preferred_language_id = l.id
            WHERE u.telegram_user_id = $1
            """,
            telegram_user_id
        )
    return row["code"] if row else None


async def set_user_language(telegram_user_id: int, language_code: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        language_row = await conn.fetchrow(
            "SELECT id FROM languages WHERE code = $1",
            language_code
        )
        if language_row:
            await conn.execute(
                """
                UPDATE users
                SET preferred_language_id = $1, user_language = $2
                WHERE telegram_user_id = $3
                """,
                language_row["id"], language_code, telegram_user_id
            )
