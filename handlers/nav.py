from aiogram import types, Router
from markup.keyboards import get_anime_selection_keyboard
from cache.anime_cache import anime_cache

navigation_router = Router()


@navigation_router.callback_query(lambda c: c.data.startswith("back_to_menu"))
async def back_to_main_menu(callback: types.CallbackQuery):
    from markup.keyboards import get_main_menu_keyboard

    text = "Этот бот выдает информацию об аниме по его названию. Выберите действие:"
    keyboard = get_main_menu_keyboard()

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=keyboard)
    else:
        await callback.message.edit_text(text, reply_markup=keyboard)

    await callback.answer()


@navigation_router.callback_query(lambda c: c.data.startswith("back_to_search"))
async def back_to_search(callback: types.CallbackQuery):

    text = "Введите название аниме для поиска:"

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text)
    else:
        await callback.message.edit_text(text)

    await callback.answer()


@navigation_router.callback_query(lambda c: c.data.startswith("back_to_selection"))
async def back_to_selection(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    last_search = await anime_cache.get_user_last_search(user_id)
    if not last_search:
        await callback.answer("Результаты поиска не найдены. Поищите заново", show_alert=True)
        return

    query = last_search['query']
    results = last_search['results']
    keyboard = get_anime_selection_keyboard(results)

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(f"🔍 Результаты поиска для «{query}»:", reply_markup=keyboard)
    else:
        await callback.message.edit_text(f"🔍 Результаты поиска для «{query}»:", reply_markup=keyboard)

    await callback.answer()