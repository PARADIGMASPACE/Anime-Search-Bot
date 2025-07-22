from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger


def get_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Поиск", callback_data="search_mode"),
            InlineKeyboardButton(text="⭐ Мои подписки", callback_data="show_favorites")
        ]
    ])


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
        anime_type = result.get('kind', '').lower()
        sticker = type_stickers.get(anime_type, '📱')

        button_text = f"{sticker} {result['russian']}"
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"view_anime:{result['id']}"
        )])

    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_search"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_anime_menu_keyboard(shikimori_id: int, is_favorite: bool, anime_id: int = None, from_favorites: bool = False) -> InlineKeyboardMarkup:
    if is_favorite and anime_id:
        action = "remove_fav"
        action_id = f"{anime_id}:{shikimori_id}"
    else:
        action = "add_favorite"
        action_id = shikimori_id

    text = "Удалить из избранного" if is_favorite else "Добавить в избранное"

    back_action = "show_favorites" if from_favorites else "back_to_selection"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=f"{action}:{action_id}")],
        [InlineKeyboardButton(text="Назад", callback_data=back_action)]
    ])

def get_favorites_list_keyboard(favorites_list):
    buttons = []
    for fav in favorites_list:
        logger.info(fav)
        title = fav.get("title_ru", "anime_title") or "Без названия"
        if len(title) > 35:
            title = title[:32] + "..."
        buttons.append([
            InlineKeyboardButton(
                text=f"📺 {title}",
                callback_data=f"view_anime:from_favorites:{fav['id_shikimori']}"
            ),
            InlineKeyboardButton(
                text="❌",
                callback_data=f"remove_fav:{fav['anime_id']}"
            )
        ])

    if favorites_list:
        buttons.append([InlineKeyboardButton(text="🗑 Очистить все", callback_data="clear_favorites")])

    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)