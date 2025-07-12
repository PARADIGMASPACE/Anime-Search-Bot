import asyncio
import os
from aiogram.types import BotCommandScopeDefault
from aiogram import Bot, Dispatcher, types
from dotenv import find_dotenv, load_dotenv
from common.scheduler import start_scheduler
from handlers.headers import anime_routrer
from common.commands_bot import commands
from middleware.antiflood import AntiFloodMiddleware

load_dotenv(find_dotenv())

bot = Bot(token=os.getenv("TOKEN"))

dp = Dispatcher()
dp.message.middleware(AntiFloodMiddleware(rate_limit=3.0))
dp.callback_query.middleware(AntiFloodMiddleware(rate_limit=1.0))
dp.include_router(anime_routrer)

async def main():
    await bot.set_my_commands(commands, scope=types.BotCommandScopeDefault())
    start_scheduler()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())