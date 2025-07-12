import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database.database import get_db_pool
from api.shikimori import json_with_anime_info_shikimori
from api.anilist import get_data_release_anime

bot = Bot(token=os.getenv("TOKEN"))


async def check_new_episodes():
    from datetime import datetime

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, anime_id, anime_title, original_title, last_episode FROM favorites"
        )

        for row in rows:
            search_title = row["original_title"] or row["anime_title"]

            data_anil = await json_with_anime_info_shikimori(search_title)
            status = data_anil.get("status", "").lower()

            if status in ["released", "завершено"]:
                # Для завершенных аниме берем количество эпизодов из Shikimori
                latest_ep = data_anil.get("episodes_count", 0) or 0
            else:
                # Для онгоингов ищем последний вышедший эпизод в AniList
                latest_ep = 0
                original_title = data_anil.get("title_en") or search_title
                data_list = await get_data_release_anime(original_title)
                if data_list is not None:
                    media = data_list.get("data", {}).get("Media") or {}
                    nodes = media.get("airingSchedule", {}).get("nodes", [])

                    # Фильтруем только уже вышедшие эпизоды
                    now = datetime.now().timestamp()
                    aired_episodes = [
                        node for node in nodes
                        if node.get("airingAt", 0) <= now
                    ]

                    if aired_episodes:
                        latest_ep = max((n.get("episode", 0) for n in aired_episodes), default=0)

            current_last_episode = row["last_episode"] or 0

            if latest_ep > current_last_episode:
                await conn.execute(
                    "UPDATE favorites SET last_episode = $1 WHERE user_id = $2 AND anime_id = $3",
                    latest_ep, row["user_id"], row["anime_id"]
                )

                if current_last_episode > 0:
                    await bot.send_message(
                        row["user_id"],
                        f"Вышла новая серия ({latest_ep}) аниме: {row['anime_title']}!"
                    )


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_new_episodes,
        "cron",
        hour=6,
        minute=0,
        max_instances=10
    )
    scheduler.add_job(
        check_new_episodes,
        "cron",
        hour=18,
        minute=0,
        max_instances=10
    )
    scheduler.start()