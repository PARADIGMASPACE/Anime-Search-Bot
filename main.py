import asyncio
import os
from aiogram.types import BotCommandScopeDefault
from aiogram import Bot, Dispatcher, types
from dotenv import find_dotenv, load_dotenv
from scheduler import start_scheduler
from common.commands_bot import commands

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
    await redis_client.connect()

    try:
        await bot.set_my_commands(commands, scope=types.BotCommandScopeDefault())
        await bot.delete_webhook(drop_pending_updates=True)
        start_scheduler(bot)
        await dp.start_polling(bot)
    finally:
        await redis_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
