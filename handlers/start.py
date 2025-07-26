from aiogram import types, Router, F
from aiogram.filters import CommandStart, Command
from markup.keyboards import get_main_menu_keyboard
from utils.i18n import i18n

router = Router()


@router.message(CommandStart())
async def start(message: types.Message):
    lang = "ru"
    await message.answer(
        i18n.t("main_menu.info", lang=lang),
        reply_markup=get_main_menu_keyboard()
    )
    await message.delete()


@router.callback_query(lambda c: c.data.startswith("search_mode"))
async def handle_anime_view(callback: types.CallbackQuery):
    lang = "ru"
    await callback.message.edit_text(i18n.t("main_menu.search_write", lang=lang))
    await callback.answer()