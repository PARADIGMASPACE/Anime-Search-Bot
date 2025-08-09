from aiogram import types, Router
from aiogram.filters import CommandStart, Command
from loguru import logger
from markup.keyboards import (
    get_main_menu_keyboard,
    get_language_keyboard,
    update_language_keyboard,
)
from utils.i18n import i18n
from cache.user_cache import user_cache
from database.users import upsert_user, update_user_language

router = Router()


@router.message(CommandStart())
async def start(message: types.Message, lang: str | None):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    logger.info(
        f"Handler 'start' started | user_id: {user_id} | username: @{username} | has_lang: {lang is not None}"
    )

    try:
        if lang:
            await message.answer(
                i18n.t("main_menu.info", lang=lang),
                reply_markup=get_main_menu_keyboard(lang),
            )
            logger.info(
                f"Handler 'start' completed | user_id: {user_id} | action: main_menu_shown"
            )
        else:
            await message.answer(
                text=i18n.t("keyboard.language_select"),
                reply_markup=get_language_keyboard(),
            )
            logger.info(
                f"Handler 'start' completed | user_id: {user_id} | action: language_selection_shown"
            )
    except Exception as e:
        logger.error(f"Handler 'start' failed | user_id: {user_id} | error: {e}")


@router.message(Command("language"))
async def change_language(message: types.Message, lang: str):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    logger.info(
        f"Handler 'change_language' started | user_id: {user_id} | username: @{username} | current_lang: {lang}"
    )

    try:
        if lang:
            await message.answer(
                i18n.t("keyboard.update_language", lang=lang),
                reply_markup=update_language_keyboard(lang),
            )
            logger.info(
                f"Handler 'change_language' completed | user_id: {user_id} | action: update_keyboard_shown"
            )
        else:
            await message.answer(
                text=i18n.t("keyboard.language_select"),
                reply_markup=get_language_keyboard(),
            )
            logger.info(
                f"Handler 'change_language' completed | user_id: {user_id} | action: language_selection_shown"
            )
    except Exception as e:
        logger.error(
            f"Handler 'change_language' failed | user_id: {user_id} | error: {e}"
        )


@router.callback_query(lambda c: c.data.startswith("update_language"))
async def update_language(callback: types.CallbackQuery, lang: str):
    user_id = callback.from_user.id
    username = callback.from_user.username or "no_username"
    callback_data = callback.data

    logger.info(
        f"Handler 'update_language' started | user_id: {user_id} | username: @{username} | data: {callback_data}"
    )

    try:
        _, lang_from_callback = callback.data.split(":")

        if lang_from_callback == lang:
            await callback.message.answer(
                text=i18n.t("keyboard.warning_user", lang=lang)
            )
            logger.info(
                f"Handler 'update_language' completed | user_id: {user_id} | action: same_language_warning | lang: {lang}"
            )
            return

        await update_user_language(user_id, lang_from_callback)
        await user_cache.user_language(user_id, lang_from_callback)
        await callback.message.edit_text(
            text=i18n.t("keyboard.successful_update", lang=lang_from_callback),
            reply_markup=get_main_menu_keyboard(lang=lang_from_callback),
        )

        logger.info(
            f"Handler 'update_language' completed | user_id: {user_id} | old_lang: {lang} | new_lang: {lang_from_callback}"
        )

    except Exception as e:
        logger.error(
            f"Handler 'update_language' failed | user_id: {user_id} | data: {callback_data} | error: {e}"
        )


@router.callback_query(lambda c: c.data.startswith("set_language"))
async def set_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "no_username"
    callback_data = callback.data

    logger.info(
        f"Handler 'set_language' started | user_id: {user_id} | username: @{username} | data: {callback_data}"
    )

    try:
        _, lang = callback.data.split(":")

        await upsert_user(user_id, lang)
        await user_cache.user_language(user_id, lang)
        await callback.message.edit_text(
            text=i18n.t("main_menu.info", lang=lang),
            reply_markup=get_main_menu_keyboard(lang),
        )

        logger.info(
            f"Handler 'set_language' completed | user_id: {user_id} | selected_lang: {lang} | action: user_created"
        )

    except Exception as e:
        logger.error(
            f"Handler 'set_language' failed | user_id: {user_id} | data: {callback_data} | error: {e}"
        )


@router.callback_query(lambda c: c.data.startswith("search_mode"))
async def handle_search_mode(callback: types.CallbackQuery, lang: str | None):
    user_id = callback.from_user.id
    username = callback.from_user.username or "no_username"

    logger.info(
        f"Handler 'handle_search_mode' started | user_id: {user_id} | username: @{username}"
    )

    try:
        await callback.message.edit_text(i18n.t("main_menu.search_write", lang=lang))
        await callback.answer()

        logger.info(
            f"Handler 'handle_search_mode' completed | user_id: {user_id} | action: search_prompt_shown"
        )

    except Exception as e:
        logger.error(
            f"Handler 'handle_search_mode' failed | user_id: {user_id} | error: {e}"
        )
