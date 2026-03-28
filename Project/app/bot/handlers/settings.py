"""Settings handlers - main menu and navigation coordinator.

This module serves as the coordinator for all settings-related operations.
Specific functionality is delegated to specialized service modules following SOLID principles:
- API settings: api_settings.py
- PIN settings: pin_settings.py  
- Security settings (2FA): security_settings.py
- Trading mode: trading_mode.py
"""
from aiogram.filters import StateFilter
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.states import AuthState, SettingsState
from app.bot.keyboards.inline import get_settings_keyboard, get_back_to_settings_keyboard
from app.bot.keyboards.reply import remove_menu
from app.bot.services import SettingsService

# Import specialized routers
from .api_settings import api_settings_router
from .pin_settings import pin_settings_router
from .security_settings import security_settings_router
from .trading_mode import trading_mode_router

settings_router = Router()

# Include all specialized sub-routers
settings_router.include_router(api_settings_router)
settings_router.include_router(pin_settings_router)
settings_router.include_router(security_settings_router)
settings_router.include_router(trading_mode_router)


def _format_settings_menu(user_id: int, api_status: str = "Connected") -> str:
    """Format the main settings menu text."""
    return (
        f"**Settings Menu**\n\n"
        f"Telegram ID: {user_id}\n"
        f"API Status: {api_status}\n"
        f"Choose an option below:"
    )


@settings_router.message(F.text == "SETTINGS", AuthState.unlocked)
async def show_settings_menu(message: types.Message, state: FSMContext):
    """Show main settings menu."""
    user_id = message.from_user.id

    SettingsService.log_user_action(
        user_id, message.from_user.username, "opened settings menu"
    )

    await state.clear()
    await state.set_state(AuthState.unlocked)

    await message.answer(
        text=_format_settings_menu(user_id),
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )


@settings_router.callback_query(F.data == "settings_lock", AuthState.unlocked)
async def process_settings_lock(callback: types.CallbackQuery, state: FSMContext):
    """Lock the bot and return to authentication state."""
    user_id = callback.from_user.id
    SettingsService.log_user_action(
        user_id, callback.from_user.username, "locked the bot via settings menu"
    )

    await state.clear()
    await callback.message.delete()

    await callback.message.answer(
        "Session locked. \n Enter /unlock to authenticate.",
        reply_markup=remove_menu()
    )

    await callback.answer()


@settings_router.callback_query(
    F.data == "settings_back",
    StateFilter(
        SettingsState.unlocked,
        SettingsState.waiting_for_api_key,
        SettingsState.waiting_for_secret_key,
        SettingsState.waiting_for_old_pin,
        SettingsState.waiting_for_new_pin,
        SettingsState.waiting_for_pin_for_2fa
    ))
async def process_settings_back(callback: types.CallbackQuery, state: FSMContext):
    """Handle back button - return to main settings menu."""
    user_id = callback.from_user.id
    SettingsService.log_user_action(
        user_id, callback.from_user.username, "cancelled an action and returned to settings"
    )

    await state.clear()
    await state.set_state(AuthState.unlocked)

    await callback.message.edit_text(
        text=_format_settings_menu(user_id),
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("Action cancelled.")
