import asyncpg
import asyncio
import logging
import os

from loguru import logger

_db_pool = None


async def get_db_pool():
    global _db_pool
    if _db_pool is None:
        logger.info("Creating new database connection pool")
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                _db_pool = await asyncpg.create_pool(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=int(os.getenv('DB_PORT', '5432')),
                    database=os.getenv('DB_NAME', 'postgres'),
                    user=os.getenv('DB_USER', 'root'),
                    password=os.getenv('DB_PASSWORD', 'root'),
                    min_size=1,
                    max_size=5,
                    command_timeout=60
                )
                logger.info(f"Database pool created successfully | attempt: {attempt + 1}")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Failed to create database pool after {max_retries} attempts: {e}")
                    raise
                logging.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(retry_delay * (attempt + 1))
    else:
        logger.debug("Using existing database pool")

    return _db_pool
