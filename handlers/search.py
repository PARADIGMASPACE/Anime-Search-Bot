from aiogram import types, Router, F
from aiogram.types import InputMediaPhoto

from api.shikimori import get_many_info_about_anime_from_shikimori
from cache.search_cache import search_cache
from cache.anime_cache import anime_cache
from database.anime import existing_anime
from markup.keyboards import get_anime_selection_keyboard, get_anime_menu_keyboard
from services.anime_service import filter_top_anime, get_caption_and_cover_image
from database.favorites import is_favorite_anime_user

from utils.i18n import i18n

search_router = Router()


@search_router.message(F.text & ~F.text.startswith('/'))
async def handle_anime_view(message: types.Message, lang: str):
    user_id = message.from_user.id
    anime_name = message.text.replace(":", ": ")

    wait_msg = await message.answer(i18n.t("search.loading", lang=lang))
    cached_search = await search_cache.get_cached_search_results(user_id, anime_name)

    if cached_search:
        filtered_anime = cached_search["results"]
    else:
        multiple_results = await get_many_info_about_anime_from_shikimori(anime_name)
        filtered_anime = filter_top_anime(multiple_results, query=anime_name, top_n=5)
        await search_cache.cache_search_results(user_id, anime_name, filtered_anime)

    if filtered_anime:
        await search_cache.save_user_last_search(user_id, anime_name, filtered_anime)
        keyboard = get_anime_selection_keyboard(filtered_anime, lang=lang)
        await wait_msg.edit_text(
            i18n.t("search.result_select", lang=lang, query=anime_name),
            reply_markup=keyboard
        )
    else:
        await wait_msg.delete()
        await message.answer(i18n.t("search.not_found", lang=lang, query=anime_name))


@search_router.callback_query(lambda c: c.data.startswith("view_anime:"))
async def handle_anime_view(callback: types.CallbackQuery, lang: str):
    user_id = callback.from_user.id
    data_parts = callback.data.split(":")
    from_favorites = len(data_parts) >= 3 and data_parts[1] == "from_favorites"
    shikimori_id = int(data_parts[2] if from_favorites else data_parts[1])


    cached_data = await anime_cache.get_cached_anime(shikimori_id)
    if cached_data:
        caption = cached_data["caption"]
        cover_image = cached_data["cover_image"]
        anilist_id = cached_data["anilist_id"]
    else:
        caption, cover_image, anilist_id = await get_caption_and_cover_image(shikimori_id, lang=lang)
        await anime_cache.cache_anime(shikimori_id, caption, cover_image, anilist_id)

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