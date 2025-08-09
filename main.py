import asyncio
import os

from aiogram.types import BotCommandScopeDefault
from aiogram import Bot, Dispatcher, types
from dotenv import find_dotenv, load_dotenv
from loguru import logger

from scheduler import start_scheduler
from common.commands_bot import commands_ru, commands_en
from cache.redis_client import redis_client

from middleware.antiflood import AntiFloodMiddleware
from middleware.language import LanguageMiddleware

from handlers.search import search_router
from handlers.favorites import favorite_router
from handlers.start import router
from handlers.nav import navigation_router

load_dotenv(find_dotenv())

bot = Bot(token=os.getenv("TOKEN"))

dp = Dispatcher()

dp.message.middleware(LanguageMiddleware())
dp.callback_query.middleware(LanguageMiddleware())

dp.message.middleware(AntiFloodMiddleware())
dp.callback_query.middleware(AntiFloodMiddleware())

for router_module in [router, search_router, favorite_router, navigation_router]:
    dp.include_router(router_module)


async def main():
    logger.info("Bot starting initialization")

    try:
        await redis_client.connect()
        logger.info("Redis connection established")

        await bot.set_my_commands(commands_ru, scope=types.BotCommandScopeDefault(), language_code="ru")
        await bot.set_my_commands(commands_en, scope=types.BotCommandScopeDefault(), language_code="en")
        logger.info("Bot commands set for ru/en languages")

        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted, pending updates dropped")

        start_scheduler(bot)
        logger.info("Scheduler started")

        logger.info("Bot started successfully, polling initiated")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Bot startup failed | error: {e}")
        raise
    finally:
        logger.info("Bot shutdown initiated")
        await redis_client.disconnect()
        logger.info("Redis connection closed, bot stopped")


if __name__ == "__main__":
    asyncio.run(main())