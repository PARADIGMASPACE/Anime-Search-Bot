from aiogram import types, Router, F
from aiogram.filters import CommandStart, Command
from api.anilist import get_data_release_anime
from api.shikimori import json_with_anime_info_shikimori, search_multiple_anime, get_anime_by_id_shikimori
from common.formating import formating_json, build_anime_caption
from markup.keyboards import get_fav_keyboard, get_favorites_list_keyboard
from database.database import get_db_pool
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger
anime_routrer = Router()
search_cache = {}


@anime_routrer.message(CommandStart())
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Поиск", callback_data="search_mode"),
            InlineKeyboardButton(text="⭐ Мои подписки", callback_data="show_favorites")
        ]
    ])
    await message.answer(
        "Этот бот выдает информацию об аниме по его названию. Выберите действие:",
        reply_markup=keyboard
    )


@anime_routrer.message(Command("favorites"))
async def show_favorites(message: types.Message):
    user_id = message.from_user.id
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT anime_id, anime_title FROM favorites WHERE user_id = $1", user_id
        )

    if not rows:
        await message.answer("У вас нет избранных аниме.")
    else:
        favorites_list = [{"anime_id": row["anime_id"], "anime_title": row["anime_title"]} for row in rows]
        keyboard = await get_favorites_list_keyboard(favorites_list, user_id)
        await message.answer(
            f"Ваши избранные аниме ({len(favorites_list)}):\n\n"
            "Нажмите на название для просмотра информации или ❌ для удаления:",
            reply_markup=keyboard
        )


@anime_routrer.message(F.text)
async def find_anime(message: types.Message):
    wait_msg = await message.answer("Ищу аниме...")

    # Ищем множественные результаты
    multiple_results = await search_multiple_anime(message.text)

    if len(multiple_results) > 1:
        # Сохраняем результаты поиска в кеш
        search_cache[message.from_user.id] = {
            'query': message.text,
            'results': multiple_results
        }

        from markup.keyboards import get_anime_selection_keyboard
        keyboard = get_anime_selection_keyboard(multiple_results)

        await wait_msg.edit_text(
            f"🔍 Найдено несколько результатов для «{message.text}»:\n\nВыберите нужное аниме:",
            reply_markup=keyboard
        )
        return

    # Остальная логика остается без изменений...
    data_sikimori = await json_with_anime_info_shikimori(message.text)

    if not data_sikimori.get("anime_id"):
        data_list = await get_data_release_anime(message.text)
        anilist_media = data_list.get("data", {}).get("Media")
        if not anilist_media:
            await wait_msg.delete()
            await message.answer(f"Аниме «{message.text}» не найдено.")
            return

        data_sikimori["anime_id"] = anilist_media.get("id")
        title = (anilist_media.get("title", {}).get("english")
                 or anilist_media.get("title", {}).get("romaji")
                 or message.text)
        data_sikimori["title_ru"] = title
        data_sikimori["title_en"] = title

    data_list = await get_data_release_anime(data_sikimori["title_en"])
    result = await formating_json(data_sikimori, data_list)
    caption = build_anime_caption(result, data_sikimori)
    keyboard = await get_fav_keyboard(data_sikimori["anime_id"], message.from_user.id)

    if result["cover_image"]:
        await message.answer_photo(result["cover_image"], caption=caption, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)

    await wait_msg.delete()


@anime_routrer.callback_query(lambda c: c.data.startswith("select_anime:"))
async def handle_anime_selection(callback: types.CallbackQuery):
    anime_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    # Ищем картинку среди ВСЕХ результатов поиска, не только с похожим названием
    cached_cover = ""

    if user_id in search_cache:
        logger.debug(f"Search cache results: {search_cache[user_id]['results']}")

        # Сначала ищем картинку у выбранного аниме
        for result in search_cache[user_id]['results']:
            if str(result['id']) == anime_id and result.get('cover_image'):
                cached_cover = result['cover_image']
                logger.debug(f"Found cover for selected anime: {cached_cover}")
                break

        # Если у выбранного нет картинки, берем ЛЮБУЮ картинку из результатов
        if not cached_cover:
            for result in search_cache[user_id]['results']:
                if result.get('cover_image'):
                    cached_cover = result['cover_image']
                    logger.debug(f"Using cover from another anime in results: {result['name']} -> {cached_cover}")
                    break

    logger.debug(f"Final cached cover for anime {anime_id}: {cached_cover}")

    # Получаем информацию по ID из Shikimori
    anime_data = await get_anime_by_id_shikimori(anime_id)
    if not anime_data:
        await callback.answer("Ошибка получения данных")
        return

    # Обрабатываем картинку правильно
    image_url = ""

    # Приоритет: кешированная картинка -> картинка из полного запроса Shikimori
    if cached_cover:
        image_url = cached_cover
        logger.debug(f"Using cached cover: {cached_cover}")
    elif anime_data.get('image'):
        original_path = anime_data['image']['original']
        logger.debug(f"Shikimori image path: {original_path}")
        if original_path != "/assets/globals/missing_original.jpg":
            image_url = f"https://shikimori.one{original_path}"
            logger.debug(f"Using Shikimori cover: {image_url}")

    logger.debug(f"Final image_url for selection: {image_url}")

    data_sikimori = {
        "anime_id": anime_data.get('id'),
        "title_ru": anime_data.get('russian'),
        "title_en": anime_data.get('name'),
        "status": anime_data.get('status'),
        "image_url": image_url,
        "type": anime_data.get('kind'),
        "episodes_count": anime_data.get('episodes') or 0,
        "episode_duration_min": anime_data.get('duration', 0),
        "genres": [genre.get('russian') for genre in anime_data.get('genres', []) if genre.get('russian')],
        "description": anime_data.get('description', ""),
        "score": anime_data.get('score')
    }

    data_list = await get_data_release_anime(data_sikimori["title_en"])
    result = await formating_json(data_sikimori, data_list)
    caption = build_anime_caption(result, data_sikimori)
    keyboard = await get_fav_keyboard(data_sikimori["anime_id"], callback.from_user.id, from_selection=True)

    if result["cover_image"]:
        await callback.message.edit_media(
            media=types.InputMediaPhoto(
                media=result["cover_image"],
                caption=caption,
                parse_mode="HTML"
            ),
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(caption, parse_mode="HTML", reply_markup=keyboard)

    await callback.answer()


@anime_routrer.callback_query(lambda c: c.data == "back_to_search")
async def back_to_search(callback: types.CallbackQuery):
    await callback.message.edit_text("Напишите название аниме для поиска:")
    await callback.answer()


@anime_routrer.callback_query(lambda c: c.data == "back_to_selection")
async def back_to_selection(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    # Проверяем есть ли сохраненные результаты поиска
    if user_id not in search_cache:
        await callback.answer("Результаты поиска не найдены. Начните новый поиск.")

        # Проверяем тип сообщения
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer("Напишите название аниме для поиска:")
        else:
            await callback.message.edit_text("Напишите название аниме для поиска:")
        return

    cached_data = search_cache[user_id]
    from markup.keyboards import get_anime_selection_keyboard
    keyboard = get_anime_selection_keyboard(cached_data['results'])

    text = f"🔍 Найдено несколько результатов для «{cached_data['query']}»:\n\nВыберите нужное аниме:"

    # Проверяем тип сообщения и обрабатываем соответственно
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=keyboard)
    else:
        await callback.message.edit_text(text, reply_markup=keyboard)

    await callback.answer()

@anime_routrer.callback_query(lambda c: c.data == "search_mode")
async def search_mode(callback: types.CallbackQuery):
    await callback.message.edit_text("Напишите название аниме для поиска:")
    await callback.answer()


@anime_routrer.callback_query(lambda c: c.data == "show_favorites")
async def show_favorites_inline(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT anime_id, anime_title FROM favorites WHERE user_id = $1", user_id
        )

    if not rows:
        await callback.message.edit_text("У вас нет избранных аниме.")
    else:
        favorites_list = [{"anime_id": row["anime_id"], "anime_title": row["anime_title"]} for row in rows]
        keyboard = await get_favorites_list_keyboard(favorites_list, user_id)
        await callback.message.edit_text(
            f"Ваши избранные аниме ({len(favorites_list)}):\n\n"
            "Нажмите на название для просмотра информации или ❌ для удаления:",
            reply_markup=keyboard
        )
    await callback.answer()


@anime_routrer.callback_query(lambda c: c.data.startswith("show_fav:"))
async def show_anime_from_favorites(callback: types.CallbackQuery):
    anime_id = int(callback.data.split(":", 1)[1])

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        fav_anime = await conn.fetchrow(
            "SELECT anime_title FROM favorites WHERE anime_id = $1 AND user_id = $2",
            anime_id, callback.from_user.id
        )

    if not fav_anime:
        await callback.answer("Аниме не найдено в избранном!")
        return

    await callback.answer("Загружаю информацию...")

    data_sikimori = await json_with_anime_info_shikimori(fav_anime["anime_title"])
    if not data_sikimori.get("anime_id"):
        data_list = await get_data_release_anime(fav_anime["anime_title"])
        anilist_media = data_list.get("data", {}).get("Media")
        if anilist_media:
            data_sikimori["anime_id"] = anilist_media.get("id")
            title = (anilist_media.get("title", {}).get("english")
                     or anilist_media.get("title", {}).get("romaji")
                     or fav_anime["anime_title"])
            data_sikimori["title_ru"] = title
            data_sikimori["title_en"] = title

    data_list = await get_data_release_anime(data_sikimori["title_en"])
    result = await formating_json(data_sikimori, data_list)
    caption = build_anime_caption(result, data_sikimori)

    # Используем anime_id для проверки, так как мы знаем что аниме в избранном
    keyboard = await get_fav_keyboard(anime_id, callback.from_user.id, from_favorites=True)

    if result["cover_image"]:
        try:
            await callback.message.edit_media(
                media=types.InputMediaPhoto(
                    media=result["cover_image"],
                    caption=caption,
                    parse_mode="HTML"
                ),
                reply_markup=keyboard
            )
        except Exception:
            await callback.message.delete()
            await callback.message.answer_photo(
                result["cover_image"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )
    else:
        await callback.message.edit_text(
            text=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )


@anime_routrer.callback_query(lambda c: c.data == "back_to_favorites")
async def back_to_favorites_list(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT anime_id, anime_title FROM favorites WHERE user_id = $1", user_id
        )

    if not rows:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer("У вас нет избранных аниме.")
        else:
            await callback.message.edit_text("У вас нет избранных аниме.")
    else:
        favorites_list = [{"anime_id": row["anime_id"], "anime_title": row["anime_title"]} for row in rows]
        keyboard = await get_favorites_list_keyboard(favorites_list, user_id)
        text = (
            f"Ваши избранные аниме ({len(favorites_list)}):\n\n"
            "Нажмите на название для просмотра информации или ❌ для удаления:"
        )

        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(text, reply_markup=keyboard)

    await callback.answer()


@anime_routrer.callback_query(lambda c: c.data.startswith("del_from_list:"))
async def delete_from_favorites_list(callback: types.CallbackQuery):
    anime_id = int(callback.data.split(":", 1)[1])
    user_id = callback.from_user.id

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        anime_info = await conn.fetchrow(
            "SELECT anime_title FROM favorites WHERE anime_id = $1 AND user_id = $2",
            anime_id, user_id
        )

        if not anime_info:
            await callback.answer("Аниме не найдено в избранном!")
            return

        await conn.execute(
            "DELETE FROM favorites WHERE anime_id = $1 AND user_id = $2",
            anime_id, user_id
        )

        rows = await conn.fetch(
            "SELECT anime_id, anime_title FROM favorites WHERE user_id = $1", user_id
        )

    if not rows:
        await callback.message.edit_text("У вас нет избранных аниме.")
        await callback.answer(f"«{anime_info['anime_title']}» удалено из избранного!")
    else:
        favorites_list = [{"anime_id": row["anime_id"], "anime_title": row["anime_title"]} for row in rows]
        keyboard = await get_favorites_list_keyboard(favorites_list, user_id)
        await callback.message.edit_text(
            f"Ваши избранные аниме ({len(favorites_list)}):\n\n"
            "Нажмите на название для просмотра информации или ❌ для удаления:",
            reply_markup=keyboard
        )
        await callback.answer(f"«{anime_info['anime_title']}» удалено из избранного!")


@anime_routrer.callback_query(lambda c: c.data.startswith("add_fav:"))
async def add_to_favorites(callback: types.CallbackQuery):
    data_parts = callback.data.split(":")
    anime_id = int(data_parts[1])

    # Определяем контекст
    from_favorites = len(data_parts) > 2 and data_parts[2] == "from_fav"
    from_selection = len(data_parts) > 2 and data_parts[2] == "from_sel"
    from_search = len(data_parts) > 2 and data_parts[2] == "from_search"

    user_id = callback.from_user.id

    raw_caption = callback.message.caption or callback.message.text or ""
    import re
    from datetime import datetime

    match = re.search(r"<b>(.*?)</b>", raw_caption)

    if match:
        display_title = match.group(1)
    else:
        lines = raw_caption.split('\n')
        if lines:
            display_title = re.sub(r'<.*?>', '', lines[0]).strip()
        else:
            display_title = "Unknown Title"

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT anime_title FROM favorites WHERE anime_id = $1 AND user_id = $2",
            anime_id, user_id
        )

        if existing:
            await callback.answer("Уже в избранном!")
            return

        # Получаем данные из Shikimori для оригинального названия
        data_sikimori = await json_with_anime_info_shikimori(display_title)
        original_title = data_sikimori.get("title_en") or display_title
        status = data_sikimori.get("status", "").lower()

        # Устанавливаем last_episode в зависимости от статуса
        if status in ["released", "завершено"]:
            current_episodes = data_sikimori.get("episodes_count", 0) or 0
        else:
            current_episodes = 0
            data_list = await get_data_release_anime(original_title)
            if data_list is not None:
                media = data_list.get("data", {}).get("Media") or {}
                nodes = media.get("airingSchedule", {}).get("nodes", [])

                now = datetime.now().timestamp()
                aired_episodes = [
                    node for node in nodes
                    if node.get("airingAt", 0) <= now
                ]

                if aired_episodes:
                    current_episodes = max((n.get("episode", 0) for n in aired_episodes), default=0)

        await conn.execute(
            "INSERT INTO favorites (anime_id, user_id, anime_title, original_title, last_episode) VALUES ($1, $2, $3, $4, $5)",
            anime_id, user_id, display_title, original_title, current_episodes
        )

    # Обновляем клавиатуру с сохранением контекста
    new_keyboard = await get_fav_keyboard(anime_id, user_id, from_favorites=from_favorites,
                                          from_selection=from_selection, from_search=from_search)
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)
    await callback.answer("Добавлено в избранное!")


@anime_routrer.callback_query(lambda c: c.data.startswith("del_fav:"))
async def remove_from_favorites(callback: types.CallbackQuery):
    data_parts = callback.data.split(":")
    anime_id = int(data_parts[1])

    # Определяем контекст
    from_favorites = len(data_parts) > 2 and data_parts[2] == "from_fav"
    from_selection = len(data_parts) > 2 and data_parts[2] == "from_sel"
    from_search = len(data_parts) > 2 and data_parts[2] == "from_search"

    user_id = callback.from_user.id

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM favorites WHERE anime_id = $1 AND user_id = $2",
            anime_id, user_id
        )

    if result == "DELETE 0":
        await callback.answer("Аниме не найдено в избранном!")
        return

    # Обновляем клавиатуру с сохранением контекста
    new_keyboard = await get_fav_keyboard(anime_id, user_id, from_favorites=from_favorites,
                                          from_selection=from_selection, from_search=from_search)
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)
    await callback.answer("Удалено из избранного!")


@anime_routrer.message(F.text & ~F.photo & ~F.video & ~F.document & ~F.voice & ~F.audio & ~F.sticker)
async def handle_non_text_message(message: types.Message):
    await message.answer("Пожалуйста, отправь только текстовое сообщение с названием аниме.")


@anime_routrer.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_main_menu(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Поиск", callback_data="search_mode"),
            InlineKeyboardButton(text="⭐ Мои подписки", callback_data="show_favorites")
        ]
    ])

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "Этот бот выдает информацию об аниме по его названию. Выберите действие:",
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(
            "Этот бот выдает информацию об аниме по его названию. Выберите действие:",
            reply_markup=keyboard
        )

    await callback.answer()
