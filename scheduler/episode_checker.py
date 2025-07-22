import asyncio
import time

from typing import List, Dict
from loguru import logger
from aiogram import Bot

from api.anilist import get_info_about_anime_from_anilist_by_id
from database.favorites import get_anime_with_users, update_anime_episodes


async def _fetch_current_episodes_anilist(anilist_id: int) -> int:
    """Получает актуальное количество эпизодов с AniList"""
    try:
        data = await get_info_about_anime_from_anilist_by_id(anilist_id)
        episodes = data.get('data', {}).get('Media', {}).get('episodes')
        return episodes if episodes else 0
    except Exception as e:
        logger.error(f"Error fetching episodes from AniList for ID {anilist_id}: {e}")
        return 0


async def _get_latest_episodes_count(anime_data: Dict) -> int:
    """Определяет актуальное количество эпизодов из доступных источников"""
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
    """Отправляет уведомления пользователям о новых эпизодах"""
    message = (
        f"🎉 Новые эпизоды!\n\n"
        f"📺 {anime_title}\n"
        f"📊 Эпизодов: {old_episodes} → {new_episodes}\n"
    )

    tasks = []
    for user_id in user_ids:
        tasks.append(_send_notification_safe(bot, user_id, message))

    await asyncio.gather(*tasks, return_exceptions=True)


async def _send_notification_safe(bot: Bot, user_id: int, message: str) -> None:
    """Безопасно отправляет уведомление пользователю"""
    try:
        await bot.send_message(user_id, message)
        logger.info(f"Notification sent to user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to send notification to user {user_id}: {e}")


async def _notify_users_about_specific_episodes(
        bot: Bot,
        user_ids: List[int],
        anime_title: str,
        new_episodes: List[int]
) -> None:
    """Отправляет уведомления пользователям о конкретных новых эпизодах"""
    if len(new_episodes) == 1:
        message = (
            f"🆕 Новый эпизод!\n\n"
            f"📺 {anime_title}\n"
            f"🔢 Эпизод {new_episodes[0]}"
        )
    else:
        episodes_str = ", ".join(map(str, new_episodes))
        message = (
            f"🆕 Новые эпизоды!\n\n"
            f"📺 {anime_title}\n"
            f"🔢 Эпизоды: {episodes_str}"
        )

    tasks = []
    for user_id in user_ids:
        tasks.append(_send_notification_safe(bot, user_id, message))

    await asyncio.gather(*tasks, return_exceptions=True)


async def _check_anime_for_updates(bot: Bot, anime_id: int, anime_data: Dict) -> None:
    """Проверяет одно аниме на наличие новых эпизодов"""
    try:
        if not anime_data['id_anilist']:
            return

        # Получаем полную информацию с расписанием эпизодов
        anilist_data = await get_info_about_anime_from_anilist_by_id(anime_data['id_anilist'])
        if not anilist_data or 'data' not in anilist_data:
            return

        media = anilist_data['data']['Media']
        if not media or not media.get('airingSchedule', {}).get('nodes'):
            return

        current_episodes = anime_data['current_episodes']
        current_timestamp = int(time.time())

        # Находим новые эпизоды, которые уже вышли
        airing_schedule = media['airingSchedule']['nodes']
        new_episodes = []

        for episode_info in airing_schedule:
            episode_number = episode_info['episode']
            airing_timestamp = episode_info['airingAt']

            # Проверяем, что эпизод новее последнего известного и уже вышел
            if episode_number > current_episodes and airing_timestamp <= current_timestamp:
                new_episodes.append(episode_number)

        if new_episodes:
            # Сортируем эпизоды и берем максимальный номер для обновления БД
            new_episodes.sort()
            latest_episode = max(new_episodes)

            logger.info(
                f"New episodes found for {anime_data['title_original']}: "
                f"episodes {new_episodes} (updating to episode {latest_episode})"
            )

            await update_anime_episodes(anime_id, latest_episode)

            # Уведомляем о конкретных новых эпизодах
            await _notify_users_about_specific_episodes(
                bot,
                anime_data['user_ids'],
                anime_data['title_original'],
                new_episodes
            )

    except Exception as e:
        logger.error(f"Error checking anime {anime_id}: {e}")


async def check_new_episodes(bot: Bot) -> None:
    logger.info("Starting episode check task")

    try:
        anime_list = await get_anime_with_users()

        if not anime_list:
            logger.info("No anime to check")
            return

        logger.info(f"Checking {len(anime_list)} anime for updates")

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

        logger.info("Episode check task completed")

    except Exception as e:
        logger.error(f"Critical error in episode checker: {e}")
