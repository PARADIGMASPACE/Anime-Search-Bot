import asyncio
import time

from typing import List, Dict
from aiogram import Bot
from utils.i18n import i18n

from api.anilist import get_info_about_anime_from_anilist_by_id
from database.favorites import get_anime_with_users, update_anime_episodes


async def _fetch_current_episodes_anilist(anilist_id: int) -> int:
    try:
        data = await get_info_about_anime_from_anilist_by_id(anilist_id)
        episodes = data.get('data', {}).get('Media', {}).get('episodes')
        return episodes if episodes else 0
    except Exception as e:
        return 0


async def _get_latest_episodes_count(anime_data: Dict) -> int:
    tasks = []

    if anime_data['id_anilist']:
        tasks.append(_fetch_current_episodes_anilist(anime_data['id_anilist']))

    if not tasks:
        return 0

    results = await asyncio.gather(*tasks, return_exceptions=True)
    episodes_counts = [r for r in results if isinstance(r, int) and r > 0]

    return max(episodes_counts) if episodes_counts else 0


async def _notify_users_about_new_episodes(
        bot: Bot,
        user_ids: List[int],
        anime_title: str,
        old_episodes: int,
        new_episodes: int
) -> None:
    lang = "ru"
    message = i18n.t("episode_checker.notify_new", lang=lang, title=anime_title, old=old_episodes, new=new_episodes)

    tasks = []
    for user_id in user_ids:
        tasks.append(_send_notification_safe(bot, user_id, message))

    await asyncio.gather(*tasks, return_exceptions=True)


async def _send_notification_safe(bot: Bot, user_id: int, message: str) -> None:
    try:
        await bot.send_message(user_id, message)
    except Exception as e:


async def _notify_users_about_specific_episodes(
        bot: Bot,
        user_ids: List[int],
        anime_title: str,
        new_episodes: List[int]
) -> None:
    lang = "ru"
    if len(new_episodes) == 1:
        message = i18n.t("episode_checker.notify_one", lang=lang, title=anime_title, number=new_episodes[0])
    else:
        episodes_str = ", ".join(map(str, new_episodes))
        message = i18n.t("episode_checker.notify_many", lang=lang, title=anime_title, numbers=episodes_str)

    tasks = []
    for user_id in user_ids:
        tasks.append(_send_notification_safe(bot, user_id, message))

    await asyncio.gather(*tasks, return_exceptions=True)


async def _check_anime_for_updates(bot: Bot, anime_id: int, anime_data: Dict) -> None:
    try:
        if not anime_data['id_anilist']:
            return

        anilist_data = await get_info_about_anime_from_anilist_by_id(anime_data['id_anilist'])
        if not anilist_data or 'data' not in anilist_data:
            return

        media = anilist_data['data']['Media']
        if not media or not media.get('airingSchedule', {}).get('nodes'):
            return

        current_episodes = anime_data['current_episodes']
        current_timestamp = int(time.time())

        airing_schedule = media['airingSchedule']['nodes']
        new_episodes = []

        for episode_info in airing_schedule:
            episode_number = episode_info['episode']
            airing_timestamp = episode_info['airingAt']

            if episode_number > current_episodes and airing_timestamp <= current_timestamp:
                new_episodes.append(episode_number)

        if new_episodes:
            new_episodes.sort()
            latest_episode = max(new_episodes)

            await update_anime_episodes(anime_id, latest_episode)

            await _notify_users_about_specific_episodes(
                bot,
                anime_data['user_ids'],
                anime_data['title_original'],
                new_episodes
            )

    except Exception as e:


async def check_new_episodes(bot: Bot) -> None:
    lang = "ru"

    try:
        anime_list = await get_anime_with_users()

        if not anime_list:
            return


        batch_size = 3
        anime_items = list(anime_list.items())

        for i in range(0, len(anime_items), batch_size):
            batch = anime_items[i:i + batch_size]
            tasks = [
                _check_anime_for_updates(bot, anime_id, anime_data)
                for anime_id, anime_data in batch
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

            if i + batch_size < len(anime_items):
                await asyncio.sleep(5 + (time.time() % 5))


    except Exception as e:
