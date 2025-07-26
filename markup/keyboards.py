from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from math import ceil
from utils.i18n import i18n

def get_main_menu_keyboard():
    lang = "ru"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=i18n.t("keyboard.search", lang=lang), callback_data="search_mode"),
            InlineKeyboardButton(text=i18n.t("keyboard.favorites", lang=lang), callback_data="show_favorites")
        ]
    ])

def get_anime_selection_keyboard(multiple_results):
    lang = "ru"
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
        InlineKeyboardButton(text=i18n.t("keyboard.back", lang=lang), callback_data="back_to_search"),
        InlineKeyboardButton(text=i18n.t("keyboard.menu", lang=lang), callback_data="back_to_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_anime_menu_keyboard(shikimori_id: int, is_favorite: bool, anime_id: int = None,
                            from_favorites: bool = False) -> InlineKeyboardMarkup:
    lang = "ru"
    if is_favorite and anime_id:
        action = "remove_fav"
        action_id = f"{anime_id}:{shikimori_id}"
    else:
        action = "add_favorite"
        action_id = shikimori_id

    text = i18n.t("keyboard.remove_favorite", lang=lang) if is_favorite else i18n.t("keyboard.add_favorite", lang=lang)

    back_action = "show_favorites" if from_favorites else "back_to_selection"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=f"{action}:{action_id}")],
        [InlineKeyboardButton(text=i18n.t("keyboard.back", lang=lang), callback_data=back_action)]
    ])

def get_favorites_list_keyboard(favorites_list, page: int = 1, page_size: int = 15):
    lang = "ru"
    total = len(favorites_list)
    total_pages = max(1, ceil(total / page_size))
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    page_favorites = favorites_list[start:end]

    buttons = []
    for fav in page_favorites:
        title = fav.get("title_ru", fav.get("anime_title", i18n.t("keyboard.no_title", lang=lang))) or i18n.t("keyboard.no_title", lang=lang)
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

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text=i18n.t("keyboard.back", lang=lang), callback_data=f"favorites_page:{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text=i18n.t("keyboard.next", lang=lang), callback_data=f"favorites_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    if favorites_list:
        buttons.append([InlineKeyboardButton(text=i18n.t("keyboard.clear_all", lang=lang), callback_data="clear_favorites")])

    buttons.append([InlineKeyboardButton(text=i18n.t("keyboard.menu", lang=lang), callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)