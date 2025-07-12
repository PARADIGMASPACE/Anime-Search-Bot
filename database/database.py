import asyncpg

_db_pool = None

async def get_db_pool():
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            user="animeuser",
            password="animepass",
            database="animebot",
            host="db",
            port="5432"
        )
    return _db_pool