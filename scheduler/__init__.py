from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from scheduler.episode_checker import check_new_episodes

#
# def start_scheduler(bot: Bot):
#     scheduler = AsyncIOScheduler()
#     scheduler.add_job(
#         check_new_episodes,
#         trigger="cron",
#         hour=6,
#         minute=0,
#         args=[bot],
#         max_instances=10
#     )
#
#     scheduler.add_job(
#         check_new_episodes,
#         trigger="cron",
#         hour=18,
#         minute=0,
#         args=[bot],
#         max_instances=10
#     )
#
#     scheduler.start()
#

def start_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_new_episodes,
        trigger="interval",
        seconds=10,
        args=[bot],
        max_instances=10
    )

    scheduler.start()
