from database.database import get_db_pool



async def upsert_anime(anime_data: dict):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO anime (title_original, title_ru, id_anilist, id_shikimori, total_episodes_relase)
            VALUES ($1, $2, $3, $4, $5) ON CONFLICT (id_shikimori) DO
            UPDATE SET
                title_original = EXCLUDED.title_original,
                title_ru = EXCLUDED.title_ru,
                id_anilist = EXCLUDED.id_anilist,
                total_episodes_relase = EXCLUDED.total_episodes_relase
            RETURNING id
            """,
            anime_data["title_original"],
            anime_data["title_ru"],
            anime_data["id_anilist"],
            anime_data["id_shikimori"],
            anime_data["total_episodes_relase"]
        )
    return row["id"]


async def existing_anime(shikimori_id: int, anilist_id: int) -> int:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM anime WHERE id_shikimori = $1 OR id_anilist = $2",
            shikimori_id, anilist_id
        )
    if row is not None:
        return row["id"]
    return False


async def add_favorite_anime_user(anime_id: int, user_id: int):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO favorites (user_id, anime_id)
            VALUES ($1, $2) ON CONFLICT (user_id, anime_id) DO NOTHING
            """,
            user_id, anime_id
        )


async def get_favorite_anime_user(user_id: int):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        favorites = await conn.fetch(
            """
            SELECT f.anime_id,
                   a.title_original AS anime_title,
                   a.title_ru AS title_ru,
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


async def update_anime_episodes(anime_id: int, new_episodes: int) -> None:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE anime SET total_episodes_relase = $1 WHERE id = $2",
            new_episodes, anime_id
        )


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
                                       array_agg(f.user_id) as user_ids
                                FROM anime a
                                         JOIN favorites f ON a.id = f.anime_id
                                GROUP BY a.id, a.id_anilist, a.id_shikimori, a.title_original, a.title_ru, a.total_episodes_relase
                                """)
    return {
        row['id']: {
            'id_anilist': row['id_anilist'],
            'id_shikimori': row['id_shikimori'],
            'title_original': row['title_original'],
            'title_ru': row['title_ru'],
            'current_episodes': row['total_episodes_relase'],
            'user_ids': row['user_ids']
        }
        for row in rows
    }