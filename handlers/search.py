from aiogram import types, Router, F
from aiogram.types import InputMediaPhoto
from loguru import logger

from api.shikimori import get_many_info_about_anime_from_shikimori
from cache.anime_cache import anime_cache
from markup.keyboards import get_anime_selection_keyboard, get_anime_menu_keyboard
from services.anime_service import filter_top_anime, get_caption_and_cover_image
from database.favorites import is_favorite_anime_user, existing_anime


search_router = Router()


@search_router.message(F.text & ~F.text.startswith('/'))
async def handle_anime_view(message: types.Message):
    user_id = message.from_user.id
    last_msg_id = await anime_cache.get_last_bot_message_id(user_id)
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    wait_msg = await message.answer("Ищу аниме... ⏳")
    await anime_cache.save_last_bot_message_id(user_id, wait_msg.message_id)
    cached_search = await anime_cache.get_cached_search_results(user_id, message.text)

    if cached_search:
        filtered_anime = cached_search["results"]
    else:
        multiple_results = await get_many_info_about_anime_from_shikimori(message.text)
        filtered_anime = filter_top_anime(multiple_results, query=message.text, top_n=5)
        await anime_cache.cache_search_results(user_id, message.text, filtered_anime)

    if filtered_anime:
        await anime_cache.save_user_last_search(user_id, message.text, filtered_anime)
        keyboard = get_anime_selection_keyboard(filtered_anime)
        await wait_msg.edit_text(
            f"🔍 Результат для «{message.text}»:\n\nВыберите нужное аниме:",
            reply_markup=keyboard
        )
        await message.delete()
    else:
        await wait_msg.delete()
        await message.answer(f"Аниме «{message.text}» не найдено.")
        await message.delete()


@search_router.callback_query(lambda c: c.data.startswith("view_anime:"))
async def handle_anime_view(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data_parts = callback.data.split(":")
    from_favorites = False

    if len(data_parts) >= 3 and data_parts[1] == "from_favorites":
        from_favorites = True
        shikimori_id = int(data_parts[2])
    else:
        shikimori_id = int(data_parts[1])

    cached_data = await anime_cache.get_cached_anime(shikimori_id)
    if cached_data:
        caption = cached_data["caption"]
        cover_image = cached_data["cover_image"]
        anilist_id = cached_data["anilist_id"]
    else:
        caption, cover_image, anilist_id = await get_caption_and_cover_image(shikimori_id)
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
            anime_id=anime_id,
            from_favorites=from_favorites
        ),
    )

    await callback.answer()