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

async def update_anime_episodes(anime_id: int, new_episodes: int) -> None:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE anime SET total_episodes_relase = $1 WHERE id = $2",
            new_episodes, anime_id
        )
