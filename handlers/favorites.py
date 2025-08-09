from aiogram import types, Router, F
from aiogram.filters import Command
from cache.favorite_cache import favorite_cache
from cache.anime_cache import anime_cache
from database.anime import *
from loguru import logger
import traceback

from markup.keyboards import get_favorites_list_keyboard, get_anime_menu_keyboard, get_main_menu_keyboard
from database.favorites import *
from services.favorite_service import formating_data_to_db
from utils.i18n import i18n

favorite_router = Router()


@favorite_router.message(Command("favorites"))
async def show_favorites(message: types.Message, lang: str = None):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"
    logger.info(f"Handler 'show_favorites' started | user_id: {user_id} | username: @{username}")

    try:
        cached_favorites = await favorite_cache.get_cached_user_favorites(user_id)
        if cached_favorites:
            favorites_list = cached_favorites
        else:
            favorites_raw = await get_favorite_anime_user(user_id)
            favorites_list = [dict(row) for row in favorites_raw]
            if favorites_list:
                await favorite_cache.cache_user_favorites(user_id, favorites_list)
                logger.debug(f"Cached new favorites | user_id: {user_id} | count: {len(favorites_list)}")

        if not favorites_list:
            await message.answer(i18n.t("favorites.empty", lang=lang))
        else:
            keyboard = get_favorites_list_keyboard(favorites_list, lang=lang)
            await message.answer(
                i18n.t("favorites.list_title", lang=lang, count=len(favorites_list)),
                reply_markup=keyboard
            )
        logger.info(
            f"Handler 'show_favorites' completed successfully | user_id: {user_id} | favorites_count: {len(favorites_list) if favorites_list else 0}")
    except Exception as e:
        logger.error(f"Handler 'show_favorites' failed | user_id: {user_id} | error: {e}")



@favorite_router.callback_query(lambda c: c.data.startswith("show_favorites"))
async def show_favorites(callback: types.CallbackQuery, lang: str = None):
    user_id = callback.from_user.id
    cached_favorites = await favorite_cache.get_cached_user_favorites(user_id)
    if cached_favorites:
        favorite_anime = cached_favorites
    else:
        favorite_anime_raw = await get_favorite_anime_user(user_id)
        favorite_anime = [dict(row) for row in favorite_anime_raw]
        if favorite_anime:
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
        keyboard = get_favorites_list_keyboard(favorites_list, lang=lang)

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
    username = callback.from_user.username or "no_username"
    callback_data = callback.data.split(":")

    logger.info(
        f"Handler 'add_favorite' started | user_id: {user_id} | username: @{username}")
    try:
        shikimori_id = int(callback_data[1])

        cached_anime = await anime_cache.get_cached_anime(shikimori_id, lang)
        if not cached_anime:
            await callback.answer(i18n.t("favorites.not_found", lang=lang), show_alert=True)
            return

        anilist_id = cached_anime.get("anilist_id", 0)

        anime_id = await existing_anime(shikimori_id, anilist_id)

        if not anime_id:
            data = await formating_data_to_db(shikimori_id, anilist_id, lang=lang)
            if not data:
                await callback.answer(i18n.t("favorites.error", lang=lang), show_alert=True)
                return
            logger.debug(f"{data}")
            anime_id = await upsert_anime(data)
        is_already_favorite = await is_favorite_anime_user(anime_id, user_id)
        if is_already_favorite:
            await callback.answer(i18n.t("favorites.error_added", lang=lang), show_alert=True)
            return
        await add_favorite_anime_user(anime_id, user_id)
        await favorite_cache.invalidate_user_favorites(user_id)

        keyboard = get_anime_menu_keyboard(shikimori_id, is_favorite=True, lang=lang, anime_id=anime_id)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer(i18n.t("favorites.added", lang=lang))
        logger.info(f"Handler 'add_favorite' completed | user_id: {user_id} | shikimori_id: {shikimori_id}")
    except Exception as e:
        logger.error(f"Handler 'add_favorite' failed | user_id: {user_id} | error: {e}\n{traceback.format_exc()}")


@favorite_router.callback_query(lambda c: c.data.startswith("remove_fav:"))
async def remove_favorite_from_list(callback: types.CallbackQuery, lang: str = None):
    user_id = callback.from_user.id
    username = callback.from_user.username or "no_username"
    callback_data = callback.data

    logger.info(
        f"Handler 'remove_favorite_from_list' started | user_id: {user_id} | username: @{username} | data: {callback_data}")

    try:
        parts = callback.data.split(":")

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
            keyboard = get_anime_menu_keyboard(shikimori_id, is_favorite=False, lang=lang, anime_id=anime_id)
            await callback.message.edit_reply_markup(reply_markup=keyboard)
            await callback.answer(i18n.t("favorites.removed", lang=lang))
            logger.info(
                f"Handler 'remove_favorite_from_list' completed (photo context) | user_id: {user_id} | anime_id: {anime_id}")
            return

        favorites_raw = await get_favorite_anime_user(user_id)
        favorites_list = [dict(row) for row in favorites_raw]

        if not favorites_list:
            await callback.message.edit_text(
                i18n.t("favorites.empty_after_remove", lang=lang),
                reply_markup=get_main_menu_keyboard(lang=lang)
            )
        else:
            keyboard = get_favorites_list_keyboard(favorites_list, lang=lang)
            await callback.message.edit_text(
                i18n.t("favorites.list_title", lang=lang, count=len(favorites_list)),
                reply_markup=keyboard
            )
        await callback.answer(i18n.t("favorites.removed", lang=lang))

        logger.info(
            f"Handler 'remove_favorite_from_list' completed | user_id: {user_id} | anime_id: {anime_id} | remaining_favorites: {len(favorites_list)}")

    except Exception as e:
        logger.error(
            f"Handler 'remove_favorite_from_list' failed | user_id: {user_id} | data: {callback_data} | error: {e}")
        await callback.answer(i18n.t("favorites.error", lang=lang), show_alert=True)


@favorite_router.callback_query(lambda c: c.data.startswith("clear_favorites"))
async def clear_favorites(callback: types.CallbackQuery, lang: str = None):
    user_id = callback.from_user.id
    username = callback.from_user.username or "no_username"
    logger.info(
        f"Handler 'clear_favorites' started | user_id: {user_id} | username: @{username} ")
    try:
        await clear_favorites_user(user_id)
        await favorite_cache.invalidate_user_favorites(user_id)

        await callback.message.edit_text(
            i18n.t("favorites.cleared_success", lang=lang),
            reply_markup=get_main_menu_keyboard(lang=lang)
        )

        await callback.answer(i18n.t("favorites.cleared", lang=lang))
        logger.info(f"Handler 'clear_favorites' completed | {user_id}")
    except Exception as e:
        logger.error(f"Handler 'clear_favorites' failed | user_id: {user_id} | error: {e}")


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
        keyboard = get_favorites_list_keyboard(favorites_list, lang=lang, page=page)
        await callback.message.edit_text(
            i18n.t("favorites.list_title", lang=lang, count=len(favorites_list)),
            reply_markup=keyboard
        )
    await callback.answer()


@favorite_router.message(~F.text)
async def handle_media_message(message: types.Message, lang: str = None):
    await message.answer(i18n.t("favorites.search_text_only", lang=lang))
