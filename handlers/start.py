from aiogram import types, Router, F
from aiogram.filters import CommandStart, Command
from markup.keyboards import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Этот бот выдает информацию об аниме по его названию. Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(lambda c: c.data.startswith("search_mode"))
async def handle_anime_view(callback: types.CallbackQuery):
    await callback.message.edit_text("Напишите название аниме для поиска:")
    await callback.answer()
