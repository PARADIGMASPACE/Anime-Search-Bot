from aiogram import types, Router, F
from aiogram.filters import Command
from cache.favorite_cache import favorite_cache
from cache.search_cache import search_cache
from markup.keyboards import get_favorites_list_keyboard, get_anime_menu_keyboard, get_main_menu_keyboard
from database.favorites import *
from services.favorite_service import formating_data_to_db
from utils.i18n import i18n


favorite_router = Router()


@favorite_router.message(Command("favorites"))
async def show_favorites(message: types.Message, lang: str = None):
    user_id = message.from_user.id
    cached_favorites = await favorite_cache.get_cached_user_favorites(user_id)
    if cached_favorites:
        favorites_list = cached_favorites
    else:
        favorites_raw = await get_favorite_anime_user(user_id)
        favorites_list = [dict(row) for row in favorites_raw]
        await favorite_cache.cache_user_favorites(user_id, favorites_list)
    if not favorites_list:
        msg = await message.answer(i18n.t("favorites.empty", lang=lang))
        await favorite_cache.save_last_bot_message_id(user_id, msg.message_id)
    else:
        keyboard = get_favorites_list_keyboard(favorites_list)
        msg = await message.answer(
            i18n.t("favorites.list_title", lang=lang, count=len(favorites_list)),
            reply_markup=keyboard
        )
        await favorite_cache.save_last_bot_message_id(user_id, msg.message_id)


@favorite_router.callback_query(lambda c: c.data.startswith("show_favorites"))
async def show_favorites(callback: types.CallbackQuery, lang: str = None):
    user_id = callback.from_user.id

    cached_favorites = await favorite_cache.get_cached_user_favorites(user_id)
    if cached_favorites:
        favorite_anime = cached_favorites
    else:
        favorite_anime_raw = await get_favorite_anime_user(user_id)
        favorite_anime = [dict(row) for row in favorite_anime_raw]
        await favorite_cache.cache_user_favorites(user_id, favorite_anime)

    if not favorite_anime:
        text = i18n.t("favorites.empty", lang=lang)
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
        text = i18n.t("favorites.list_title", lang=lang, count=len(favorites_list))
        keyboard = get_favorites_list_keyboard(favorites_list)

    if callback.message.photo:
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
async def add_favorite(callback: types.CallbackQuery, lang: str = None):
    user_id = callback.from_user.id
    shikimori_id = int(callback.data.split(":")[1])

    cached_anime = await search_cache.get_cached_anime(shikimori_id)
    if not cached_anime:
        await callback.answer(i18n.t("favorites.not_found", lang=lang), show_alert=True)
        return

    anilist_id = cached_anime.get("anilist_id", 0)

    anime_id = await existing_anime(shikimori_id, anilist_id)
    if not anime_id:
        data = await formating_data_to_db(shikimori_id, anilist_id)
        anime_id = await upsert_anime(data)

    await add_favorite_anime_user(anime_id, user_id)
    await favorite_cache.invalidate_user_favorites(user_id)

    keyboard = get_anime_menu_keyboard(shikimori_id, is_favorite=True, anime_id=anime_id)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(i18n.t("favorites.added", lang=lang))


@favorite_router.callback_query(lambda c: c.data.startswith("remove_fav:"))
async def remove_favorite_from_list(callback: types.CallbackQuery, lang: str = None):
    parts = callback.data.split(":")
    user_id = callback.from_user.id
    if len(parts) == 3:
        anime_id = int(parts[1])
        shikimori_id = int(parts[2])
    else:
        anime_id = int(parts[1])
        shikimori_id = None

    await del_favorite_anime_user(anime_id, user_id)
    await favorite_cache.invalidate_user_favorites(user_id)

    if callback.message.photo:
        if shikimori_id is None:
            shikimori_id = 0
        keyboard = get_anime_menu_keyboard(shikimori_id, is_favorite=False, anime_id=anime_id)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer(i18n.t("favorites.removed", lang=lang))
        return

    favorites_raw = await get_favorite_anime_user(user_id)
    favorites_list = [dict(row) for row in favorites_raw]

    if not favorites_list:
        await callback.message.edit_text(
            i18n.t("favorites.empty_after_remove", lang=lang),
            reply_markup=get_main_menu_keyboard()
        )
    else:
        keyboard = get_favorites_list_keyboard(favorites_list)
        await callback.message.edit_text(
            i18n.t("favorites.list_title", lang=lang, count=len(favorites_list)),
            reply_markup=keyboard
        )
    await callback.answer(i18n.t("favorites.removed", lang=lang))


@favorite_router.callback_query(lambda c: c.data.startswith("clear_favorites"))
async def clear_favorites(callback: types.CallbackQuery, lang: str = None):
    user_id = callback.from_user.id

    await clear_favorites_user(user_id)
    await favorite_cache.invalidate_user_favorites(user_id)

    await callback.message.edit_text(
        i18n.t("favorites.cleared_success", lang=lang),
        reply_markup=get_main_menu_keyboard()
    )

    await callback.answer(i18n.t("favorites.cleared", lang=lang))


@favorite_router.callback_query(lambda c: c.data.startswith("favorites_page:"))
async def favorites_page_callback(callback: types.CallbackQuery, lang: str = None):
    user_id = callback.from_user.id
    page = int(callback.data.split(":")[1])

    cached_favorites = await favorite_cache.get_cached_user_favorites(user_id)
    if cached_favorites:
        favorites_list = cached_favorites
    else:
        favorites_raw = await get_favorite_anime_user(user_id)
        favorites_list = [dict(row) for row in favorites_raw]
        await favorite_cache.cache_user_favorites(user_id, favorites_list)

    if not favorites_list:
        await callback.message.edit_text(i18n.t("favorites.empty", lang=lang))
    else:
        keyboard = get_favorites_list_keyboard(favorites_list, page=page)
        await callback.message.edit_text(
            i18n.t("favorites.list_title", lang=lang, count=len(favorites_list)),
            reply_markup=keyboard
        )
    await callback.answer()


@favorite_router.message(~F.text)
async def handle_media_message(message: types.Message, lang: str = None):
    await message.answer(i18n.t("favorites.search_text_only", lang=lang))