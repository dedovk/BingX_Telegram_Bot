from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.states import AuthState
from app.bot.keyboards.inline import get_settings_keyboard
from app.bot.keyboards.reply import remove_menu
from app.core.config import settings
from app.bot.handlers.wallet import get_bingx_client

settings_router = Router()


@settings_router.message(F.text == "SETTINGS", AuthState.unlocked)
async def show_settings_menu(message: types.Message, state: FSMContext):
    """ """
    user_id = message.from_user.id

    logger.info(
        f"User(ID: {user_id}, Username: {message.from_user.username}) open settings menu.")

    text = (
        f"------Settings Menu------\n\n"
        f"Telegram ID: {user_id}\n"
        f"API Status: Connected\n"
        f"Choose an option below:"
    )

    await message.answer(
        text=text,
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )


@settings_router.callback_query(F.data == "settings_lock", AuthState.unlocked)
async def process_settings_lock(callback: types.CallbackQuery, state: FSMContext):
    """ """
    user_id = callback.from_user.id
    logger.info(
        f"User(ID: {user_id}, Username: {callback.from_user.username}) lock the bot via settings menu.")

    await state.clear()
    await callback.message.delete()

    await callback.message.answer(
        "Session locked. \n Enter /unlock to authenticate.",
        reply_markup=remove_menu()
    )

    await callback.answer()


@settings_router.callback_query(F.data == "settings_check_api", AuthState.unlocked)
async def process_settings_check_api(callback: types.CallbackQuery):
    """ """
    logger.info(
        f"User(ID: {callback.from_user.id}, Username: {callback.from_user.username}) checking API.")

    await callback.message.edit_text(
        f"------Settings Menu------\n\n"
        f"Telegram ID: {callback.from_user.id}\n"
        f"API Status: Checking connection...\n"
        f"Choose an option below:",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )

    try:
        client = get_bingx_client()

        await client.get_active_spot_balance()
        status_text = "Connected & Valid"
    except Exception as e:
        logger.error(f"API check failed: {e}")
        status_text = "Connection Error. Check keys."
    finally:
        await client.close_connection()

    await callback.message.edit_text(
        f"------Settings Menu------\n\n"
        f"Telegram ID: {callback.from_user.id}\n"
        f"API Status: {status_text}\n"
        f"Choose an option below:",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("API status updated.")
