from aiogram import types, Router, F
from aiogram.types import InputMediaPhoto

from api.shikimori import get_many_info_about_anime_from_shikimori
from cache.search_cache import search_cache
from database.anime import existing_anime
from markup.keyboards import get_anime_selection_keyboard, get_anime_menu_keyboard
from services.anime_service import filter_top_anime, get_caption_and_cover_image
from database.favorites import is_favorite_anime_user

from utils.i18n import i18n
from utils.utils import log_api_response

search_router = Router()


from loguru import logger

@search_router.message(F.text & ~F.text.startswith('/'))
async def handle_anime_search(message: types.Message, lang: str):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"
    anime_name = message.text.replace(":", ": ")

    logger.info(f"Handler 'handle_anime_search' started | user_id: {user_id} | username: @{username} | query: '{anime_name}'")

    try:
        wait_msg = await message.answer(i18n.t("search.loading", lang=lang))
        cached_search = await search_cache.get_cached_search_results(user_id, anime_name)

        if cached_search:
            filtered_anime = cached_search["results"]
            logger.info(f"Using cached search results | user_id: {user_id} | query: '{anime_name}' | results_count: {len(filtered_anime)}")
        else:
            multiple_results = await get_many_info_about_anime_from_shikimori(anime_name)
            filtered_anime = filter_top_anime(multiple_results, query=anime_name, top_n=5)
            await search_cache.cache_search_results(user_id, anime_name, filtered_anime)
            logger.info(f"New search performed | user_id: {user_id} | query: '{anime_name}' | results_count: {len(filtered_anime)}")

        log_api_response("filtered_anime", filtered_anime)

        if filtered_anime:
            await search_cache.save_user_last_search(user_id, anime_name, filtered_anime)
            keyboard = get_anime_selection_keyboard(filtered_anime, lang=lang)
            await wait_msg.edit_text(
                i18n.t("search.result_select", lang=lang, query=anime_name),
                reply_markup=keyboard
            )
            logger.info(f"Handler 'handle_anime_search' completed | user_id: {user_id} | results_shown: {len(filtered_anime)}")
        else:
            await wait_msg.delete()
            await message.answer(i18n.t("search.not_found", lang=lang, query=anime_name))
            logger.info(f"Handler 'handle_anime_search' completed | user_id: {user_id} | no_results_found")

    except Exception as e:
        logger.error(f"Handler 'handle_anime_search' failed | user_id: {user_id} | query: '{anime_name}' | error: {e}")
        await message.answer(i18n.t("search.error", lang=lang))


@search_router.callback_query(lambda c: c.data.startswith("view_anime:"))
async def handle_anime_view(callback: types.CallbackQuery, lang: str):
    user_id = callback.from_user.id
    username = callback.from_user.username or "no_username"
    callback_data = callback.data

    logger.info(f"Handler 'handle_anime_view' started | user_id: {user_id} | username: @{username} | data: {callback_data}")

    try:
        data_parts = callback.data.split(":")
        from_favorites = len(data_parts) >= 3 and data_parts[1] == "from_favorites"
        shikimori_id = int(data_parts[2] if from_favorites else data_parts[1])

        caption, cover_image, anilist_id, raw_data_db = await get_caption_and_cover_image(shikimori_id, lang=lang)
        anime_id = await existing_anime(shikimori_id, anilist_id or 0)

        is_favorite = False
        if anime_id is not None:
            is_favorite = await is_favorite_anime_user(anime_id, user_id)

        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=cover_image,
                caption=caption,
                parse_mode="HTML"
            ),
            reply_markup=get_anime_menu_keyboard(
                shikimori_id,
                is_favorite=is_favorite,
                lang=lang,
                anime_id=anime_id,
                from_favorites=from_favorites
            ),
        )

        await callback.answer()
        logger.info(f"Handler 'handle_anime_view' completed | user_id: {user_id} | shikimori_id: {shikimori_id} | is_favorite: {is_favorite} | from_favorites: {from_favorites}")

    except Exception as e:
        logger.error(f"Handler 'handle_anime_view' failed | user_id: {user_id} | data: {callback_data} | error: {e}")
        await callback.answer(i18n.t("search.error", lang=lang), show_alert=True)
