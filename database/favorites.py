from database.database import get_db_pool


async def get_favorite_anime_user(user_id: int):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        favorites = await conn.fetch(
            """
            SELECT f.anime_id,
                   a.title_original AS anime_title,
                   a.title_ru       AS title_ru,
                   a.id_shikimori,
                   a.id_anilist
            FROM favorites f
                     JOIN anime a ON f.anime_id = a.id
            WHERE f.user_id = $1
            """,
            user_id
        )
    return favorites


async def del_favorite_anime_user(anime_id: int, user_id: int):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM favorites WHERE anime_id = $1 AND user_id = $2",
            anime_id, user_id
        )


async def clear_favorites_user(user_id: int):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM favorites WHERE user_id = $1",
            user_id
        )


async def is_favorite_anime_user(anime_id: int, user_id: int):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT 1 FROM favorites WHERE anime_id = $1 AND user_id = $2",
            anime_id, user_id
        )
    return existing is not None


async def get_anime_with_users():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT a.id,
                   a.id_anilist,
                   a.id_shikimori,
                   a.title_original,
                   a.title_ru,
                   a.total_episodes_relase,
                   array_agg(f.user_id) as user_ids,
                   array_agg(u.user_language) as user_languages
            FROM anime a
                     JOIN favorites f ON a.id = f.anime_id
                     JOIN users u ON f.user_id = u.telegram_user_id
            GROUP BY a.id, a.id_anilist, a.id_shikimori, a.title_original, a.title_ru,
                     a.total_episodes_relase
        """)
    return {
        row['id']: {
            'id_anilist': row['id_anilist'],
            'id_shikimori': row['id_shikimori'],
            'title_original': row['title_original'],
            'title_ru': row['title_ru'],
            'current_episodes': row['total_episodes_relase'],
            'user_ids': row['user_ids'],
            'user_languages': row['user_languages']
        }
        for row in rows
    }
