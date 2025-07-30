import asyncio
import time
import random
import logging

from typing import List, Dict
from aiogram import Bot

from database.anime import update_anime_episodes
from utils.i18n import i18n

from api.anilist import get_info_about_anime_from_anilist_by_id
from database.favorites import get_anime_with_users


logger = logging.getLogger("episode_checker")


async def _send_notification_safe(bot: Bot, user_id: int, message: str) -> None:
    try:
        await bot.send_message(user_id, message)
        logger.info(f"Sent notification to user {user_id}: {message}")
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}")


async def _notify_users_about_specific_episodes(
        bot: Bot,
        user_ids: List[int],
        user_languages: List[str],
        anime_titles: Dict[str, str],
        new_episodes: List[int]
) -> None:
    logger.info(f"Notifying users {user_ids} about new episodes {new_episodes} for anime {anime_titles}")
    for user_id, lang in zip(user_ids, user_languages):
        if lang.lower() == 'ru':
            title = anime_titles.get('ru', anime_titles.get('original', ''))
        else:
            title = anime_titles.get('original', anime_titles.get('ru', ''))
        if len(new_episodes) == 1:
            message = i18n.t("episode_checker.notify_one", lang=lang, title=title, number=new_episodes[0])
        else:
            episodes_str = ", ".join(map(str, new_episodes))
            message = i18n.t("episode_checker.notify_many", lang=lang, title=title, numbers=episodes_str)
        await _send_notification_safe(bot, user_id, message)


async def _check_anime_for_updates(bot: Bot, anime_id: int, anime_data: Dict, media: Dict) -> None:
    logger.info(f"Checking anime {anime_id} for updates. Current episodes: {anime_data['current_episodes']}")
    if not media or not media.get('airingSchedule', {}).get('nodes'):
        logger.warning(f"No airing schedule found for anime {anime_id}")
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
        logger.info(f"Anime {anime_id} has new episodes: {new_episodes}")
        new_episodes.sort()
        latest_episode = max(new_episodes)

        await update_anime_episodes(anime_id, latest_episode)
        logger.info(f"Updated anime {anime_id} episodes to {latest_episode}")

        await _notify_users_about_specific_episodes(
            bot,
            anime_data['user_ids'],
            anime_data['user_languages'],
            {
                'ru': anime_data['title_ru'],
                'original': anime_data['title_original']
            },
            new_episodes
        )
    else:
        logger.info(f"No new episodes for anime {anime_id}")


async def check_new_episodes(bot: Bot) -> None:
    logger.info("Starting check_new_episodes scheduler job")
    anime_list = await get_anime_with_users()
    if not anime_list:
        logger.warning("No anime with users found for episode check")
        return

    batch_size = 3
    anime_items = list(anime_list.items())

    for i in range(0, len(anime_items), batch_size):
        batch = anime_items[i:i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1}: {batch}")

        fetch_tasks = [
            get_info_about_anime_from_anilist_by_id(anime_data['id_anilist'])
            if anime_data['id_anilist'] else None
            for _, anime_data in batch
        ]

        anilist_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        tasks = []
        for (anime_id, anime_data), result in zip(batch, anilist_results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching info for anime {anime_id}: {result}")
                continue
            if isinstance(result, dict) and 'data' in result:
                media = result['data']['Media']
                tasks.append(_check_anime_for_updates(bot, anime_id, anime_data, media))
            else:
                logger.warning(f"No valid data for anime {anime_id}")

        await asyncio.gather(*tasks, return_exceptions=True)

        if i + batch_size < len(anime_items):
            sleep_time = random.uniform(5, 10)
            logger.info(f"Sleeping for {sleep_time:.2f} seconds before next batch")
            await asyncio.sleep(sleep_time)
