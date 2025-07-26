from aiogram import types, Router, F
from aiogram.filters import Command
from cache.anime_cache import anime_cache
from markup.keyboards import get_favorites_list_keyboard, get_anime_menu_keyboard, get_main_menu_keyboard
from database.favorites import *
from services.favorite_service import formating_data_to_db

favorite_router = Router()


@favorite_router.message(Command("favorites"))
async def show_favorites(message: types.Message):
    user_id = message.from_user.id
    last_msg_id = await anime_cache.get_last_bot_message_id(user_id)
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    cached_favorites = await anime_cache.get_cached_user_favorites(user_id)
    if cached_favorites:
        favorites_list = cached_favorites
    else:
        favorites_raw = await get_favorite_anime_user(user_id)
        favorites_list = [dict(row) for row in favorites_raw]
        await anime_cache.cache_user_favorites(user_id, favorites_list)
    if not favorites_list:
        msg = await message.answer("У вас нет избранных аниме.")
        await anime_cache.save_last_bot_message_id(user_id, msg.message_id)
    else:
        keyboard = get_favorites_list_keyboard(favorites_list)
        msg = await message.answer(
            f"Ваши избранные аниме ({len(favorites_list)}):\n\n"
            "Нажмите на название для просмотра информации или ❌ для удаления:",
            reply_markup=keyboard
        )
        await anime_cache.save_last_bot_message_id(user_id, msg.message_id)
    await message.delete()

@favorite_router.callback_query(lambda c: c.data.startswith("show_favorites"))
async def show_favorites(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    cached_favorites = await anime_cache.get_cached_user_favorites(user_id)
    if cached_favorites:
        favorite_anime = cached_favorites
    else:
        favorite_anime_raw = await get_favorite_anime_user(user_id)
        favorite_anime = [dict(row) for row in favorite_anime_raw]
        await anime_cache.cache_user_favorites(user_id, favorite_anime)

    if not favorite_anime:
        text = "У вас нет избранных аниме."
        keyboard = None
    else:
        favorites_list = [
            {
                "anime_id": row["anime_id"],
                "anime_title": row["anime_title"],
                "id_shikimori": row["id_shikimori"],
                "title_ru": row.get("title_ru")
            }
            for row in favorite_anime
        ]
        text = (
            f"Ваши избранные аниме ({len(favorites_list)}):\n\n"
            "Нажмите на название для просмотра информации или ❌ для удаления:"
        )
        keyboard = get_favorites_list_keyboard(favorites_list)

    if callback.message.photo:
        await callback.message.delete()
        if keyboard:
            await callback.message.answer(text, reply_markup=keyboard)
        else:
            await callback.message.answer(text)
    else:
        if keyboard:
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(text)

    await callback.answer()

@favorite_router.callback_query(lambda c: c.data.startswith("add_favorite:"))
async def add_favorite(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    shikimori_id = int(callback.data.split(":")[1])

    cached_anime = await anime_cache.get_cached_anime(shikimori_id)
    if not cached_anime:
        await callback.answer("Данные аниме не найдены в кеше", show_alert=True)
        return

    anilist_id = cached_anime.get("anilist_id", 0)

    anime_id = await existing_anime(shikimori_id, anilist_id)
    if not anime_id:
        data = await formating_data_to_db(shikimori_id, anilist_id)
        anime_id = await upsert_anime(data)

    await add_favorite_anime_user(anime_id, user_id)
    await anime_cache.invalidate_user_favorites(user_id)

    keyboard = get_anime_menu_keyboard(shikimori_id, is_favorite=True, anime_id=anime_id)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer("Добавлено в избранное")

@favorite_router.callback_query(lambda c: c.data.startswith("remove_fav:"))
async def remove_favorite_from_list(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    user_id = callback.from_user.id
    if len(parts) == 3:
        anime_id = int(parts[1])
        shikimori_id = int(parts[2])
    else:
        anime_id = int(parts[1])
        shikimori_id = None

    await del_favorite_anime_user(anime_id, user_id)
    await anime_cache.invalidate_user_favorites(user_id)

    if callback.message.photo:
        if shikimori_id is None:
            shikimori_id = 0
        keyboard = get_anime_menu_keyboard(shikimori_id, is_favorite=False, anime_id=anime_id)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer("Удалено из избранного")
        return

    favorites_raw = await get_favorite_anime_user(user_id)
    favorites_list = [dict(row) for row in favorites_raw]

    if not favorites_list:
        await callback.message.edit_text(
            "Ваш список избранного пуст. Выберите действие:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        keyboard = get_favorites_list_keyboard(favorites_list)
        await callback.message.edit_text(
            f"Ваши избранные аниме ({len(favorites_list)}):\n\n"
            "Нажмите на название для просмотра информации или ❌ для удаления:",
            reply_markup=keyboard
        )
    await callback.answer("Удалено из избранного")

@favorite_router.callback_query(lambda c: c.data.startswith("clear_favorites"))
async def clear_favorites(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    await clear_favorites_user(user_id)
    await anime_cache.invalidate_user_favorites(user_id)

    await callback.message.edit_text(
        "Ваш список избранного успешно очищен! Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )

    await callback.answer("Список избранного очищен")


@favorite_router.message(~F.text)
async def handle_media_message(message: types.Message):
    await message.answer("Для поиска аниме отправьте текстовое сообщение с названием.")
