from aiogram import types, Router
from markup.keyboards import get_anime_selection_keyboard
from cache.anime_cache import anime_cache
from utils.i18n import i18n
from markup.keyboards import get_main_menu_keyboard

navigation_router = Router()


@navigation_router.callback_query(lambda c: c.data.startswith("back_to_menu"))
async def back_to_main_menu(callback: types.CallbackQuery, lang: str = None):

    text = i18n.t("main_menu.info", lang=lang)
    keyboard = get_main_menu_keyboard()

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=keyboard)
    else:
        await callback.message.edit_text(text, reply_markup=keyboard)

    await callback.answer()


@navigation_router.callback_query(lambda c: c.data.startswith("back_to_search"))
async def back_to_search(callback: types.CallbackQuery, lang: str = None):
    text = i18n.t("main_menu.search_write", lang=lang)

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text)
    else:
        await callback.message.edit_text(text)

    await callback.answer()


@navigation_router.callback_query(lambda c: c.data.startswith("back_to_selection"))
async def back_to_selection(callback: types.CallbackQuery, lang: str = None):
    user_id = callback.from_user.id

    last_search = await anime_cache.get_user_last_search(user_id)
    if not last_search:
        await callback.answer(i18n.t("search.no_results", lang=lang), show_alert=True)
        return

    query = last_search['query']
    results = last_search['results']
    keyboard = get_anime_selection_keyboard(results)

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(i18n.t("search.result_title", lang=lang, query=query), reply_markup=keyboard)
    else:
        await callback.message.edit_text(i18n.t("search.result_title", lang=lang, query=query), reply_markup=keyboard)

    await callback.answer()