from aiogram import types, Router
from aiogram.filters import CommandStart, Command

from markup.keyboards import get_main_menu_keyboard, get_language_keyboard, update_language_keyboard
from utils.i18n import i18n
from cache.user_cache import user_cache
from database.users import upsert_user, update_user_language

router = Router()


@router.message(CommandStart())
async def start(message: types.Message, lang: str | None):
    if lang:
        await message.answer(
            i18n.t("main_menu.info", lang=lang),
            reply_markup=get_main_menu_keyboard(lang)
        )
    else:
        await message.answer(
            text=i18n.t("keyboard.language_select"),
            reply_markup=get_language_keyboard()
        )


@router.message(Command("language"))
async def change_language(message: types.Message, lang: str):
    if lang:
        await message.answer(
            i18n.t("keyboard.update_language", lang=lang),
            reply_markup=update_language_keyboard(lang)
        )
    else:
        await message.answer(
            text=i18n.t("keyboard.language_select"),
            reply_markup=get_language_keyboard()
        )


@router.callback_query(lambda c: c.data.startswith("update_language"))
async def update_language(callback: types.CallbackQuery, lang: str):
    user_id = callback.from_user.id
    _, lang_from_callback = callback.data.split(":")
    if lang_from_callback == lang:
        await callback.message.answer(
            text=i18n.t("keyboard.warning_user", lang=lang)
        )
        return
    await update_user_language(user_id, lang_from_callback)
    await user_cache.user_language(user_id, lang_from_callback)
    await callback.message.answer(
        text=i18n.t("keyboard.successful_update", lang=lang_from_callback),
    )


@router.callback_query(lambda c: c.data.startswith("set_language"))
async def set_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    _, lang = callback.data.split(":")
    await upsert_user(user_id, lang)
    await user_cache.user_language(user_id, lang)
    await callback.message.answer(
        i18n.t("main_menu.info", lang=lang),
        reply_markup=get_main_menu_keyboard(lang)
    )


@router.callback_query(lambda c: c.data.startswith("search_mode"))
async def handle_anime_view(callback: types.CallbackQuery, lang: str | None):
    await callback.message.edit_text(
        i18n.t("main_menu.search_write", lang=lang)
    )
    await callback.answer()


