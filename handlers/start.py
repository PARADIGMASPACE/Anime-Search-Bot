from aiogram import types, Router, F
from aiogram.filters import CommandStart, Command
from markup.keyboards import get_main_menu_keyboard, get_language_keyboard
from utils.i18n import i18n
from cache.anime_cache import anime_cache
from database.users import get_user_language, upsert_user, set_user_language
router = Router()


@router.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    user_language = await anime_cache.get_user_language(user_id)
    if user_language:
        await message.answer(
            i18n.t("main_menu.info", lang=user_language),
            reply_markup=get_main_menu_keyboard(user_language)
        )
        return
    user_language_from_db = await get_user_language(user_id)
    if user_language_from_db:
        await anime_cache.user_language(user_id, user_language_from_db)
        await message.answer(
            i18n.t("main_menu.info", lang=user_language_from_db),
            reply_markup=get_main_menu_keyboard(user_language_from_db)
        )
        return
    await message.answer(text=i18n.t("keyboard.language_select"), reply_markup=get_language_keyboard())

@router.callback_query(lambda c: c.data.startswith("set_language"))
async def set_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data_parts = callback.data.split(":")
    lang = data_parts[1]
    await upsert_user(user_id, lang)
    await anime_cache.user_language(user_id, lang)
    await callback.message.answer(
        i18n.t("main_menu.info", lang=lang),
        reply_markup=get_main_menu_keyboard(lang)
    )

@router.callback_query(lambda c: c.data.startswith("search_mode"))
async def handle_anime_view(callback: types.CallbackQuery):
    lang = "ru"
    await callback.message.edit_text(i18n.t("main_menu.search_write", lang=lang))
    await callback.answer()