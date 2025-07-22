import redis.asyncio as redis
import json
import os
from typing import Optional, Any
from loguru import logger


class RedisClient:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', '6379'))

    async def connect(self):
        """Подключение к Redis"""
        try:
            self.redis = redis.Redis(
                host=self.host,
                port=self.port,
                decode_responses=True
            )
            await self.redis.ping()
            logger.info(f"Подключен к Redis на {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Ошибка подключения к Redis: {e}")
            raise

    async def disconnect(self):
        """Отключение от Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Отключен от Redis")

    async def set(self, key: str, value: Any, expire: int = 3600):
        """Установка значения с TTL"""
        if not self.redis:
            await self.connect()

        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)

        await self.redis.set(key, value, ex=expire)

    async def get(self, key: str) -> Optional[Any]:
        """Получение значения"""
        if not self.redis:
            await self.connect()

        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def delete(self, key: str):
        """Удаление ключа"""
        if not self.redis:
            await self.connect()

        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        if not self.redis:
            await self.connect()

        return await self.redis.exists(key)


# Глобальный экземпляр
redis_client = RedisClient()