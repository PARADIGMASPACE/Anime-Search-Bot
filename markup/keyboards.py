from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.database import get_db_pool


async def get_fav_keyboard(anime_id: int, user_id: int, from_favorites: bool = False, from_search: bool = False,
                           from_selection: bool = False):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT anime_title FROM favorites WHERE anime_id = $1 AND user_id = $2",
            anime_id, user_id
        )

    buttons = []

    if existing:
        context = ""
        if from_favorites:
            context = ":from_fav"
        elif from_selection:
            context = ":from_sel"
        elif from_search:
            context = ":from_search"

        buttons.append([InlineKeyboardButton(
            text="❌ Удалить из избранного",
            callback_data=f"del_fav:{anime_id}{context}"
        )])
    else:
        context = ""
        if from_favorites:
            context = ":from_fav"
        elif from_selection:
            context = ":from_sel"
        elif from_search:
            context = ":from_search"

        buttons.append([InlineKeyboardButton(
            text="⭐ Добавить в избранное",
            callback_data=f"add_fav:{anime_id}{context}"
        )])

    if from_favorites:
        buttons.append([InlineKeyboardButton(
            text="⬅️ Назад к списку",
            callback_data="back_to_favorites"
        )])
    elif from_selection:
        buttons.append([InlineKeyboardButton(
            text="⬅️ Назад к выбору",
            callback_data="back_to_selection"
        )])

    buttons.append([InlineKeyboardButton(
        text="🏠 Главное меню",
        callback_data="back_to_menu"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_favorites_list_keyboard(favorites_list, user_id):
    buttons = []

    for fav in favorites_list:
        title = fav["anime_title"]
        if len(title) > 35:
            title = title[:32] + "..."

        buttons.append([
            InlineKeyboardButton(
                text=title,
                callback_data=f"show_fav:{fav['anime_id']}"
            ),
            InlineKeyboardButton(
                text="❌",
                callback_data=f"del_from_list:{fav['anime_id']}"
            )
        ])

    buttons.append([InlineKeyboardButton(
        text="🏠 Главное меню",
        callback_data="back_to_menu"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_anime_selection_keyboard(multiple_results):
    type_stickers = {
        'tv': '📺',
        'movie': '🎬',
        'ova': '📀',
        'ona': '💻',
        'special': '✨',
        'music': '🎵'
    }

    buttons = []
    for result in multiple_results:
        anime_type = result.get('type', '').lower()
        sticker = type_stickers.get(anime_type, '📱')
        episodes_text = f"{result['episodes']} эп." if result['episodes'] else "? эп."

        button_text = f"{sticker} {result['name']} ({episodes_text})"
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"select_anime:{result['id']}"
        )])

    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_search"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)