"""Trading mode handlers - manage live/sandbox mode switching UI."""
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.states import AuthState, SettingsState
from app.bot.keyboards.inline import get_back_to_settings_keyboard
from app.bot.services import TradingModeService, SettingsService

trading_mode_router = Router()


@trading_mode_router.callback_query(F.data == "settings_trading_mode", AuthState.unlocked)
async def show_trading_mode_menu(callback: types.CallbackQuery, state: FSMContext):
    """Show trading mode information and switching options."""
    user_id = callback.from_user.id

    SettingsService.log_user_action(
        user_id, callback.from_user.username, "accessed trading mode menu"
    )

    mode_info = TradingModeService.get_mode_info()

    await callback.message.edit_text(
        text=mode_info,
        reply_markup=_get_trading_mode_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@trading_mode_router.callback_query(F.data == "mode_switch_sandbox", AuthState.unlocked)
async def process_switch_to_sandbox(callback: types.CallbackQuery, state: FSMContext):
    """Switch to sandbox/demo mode."""
    user_id = callback.from_user.id

    success, message = await TradingModeService.switch_trading_mode("sandbox")

    if success:
        SettingsService.log_user_action(
            user_id, callback.from_user.username, "switched to sandbox mode"
        )
        await callback.message.edit_text(
            text=f"✅ {message}\n\n{TradingModeService.get_mode_info()}",
            reply_markup=_get_trading_mode_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("Mode switched!")
    else:
        await callback.message.edit_text(
            text=f"❌ {message}\n\n{TradingModeService.get_mode_info()}",
            reply_markup=_get_trading_mode_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer(message, show_alert=True)


@trading_mode_router.callback_query(F.data == "mode_switch_live", AuthState.unlocked)
async def process_switch_to_live(callback: types.CallbackQuery, state: FSMContext):
    """Switch to live mode - with confirmation."""
    user_id = callback.from_user.id

    await callback.answer(
        text="⚠️ You are about to switch to LIVE trading mode. Be careful!",
        show_alert=True
    )

    success, message = await TradingModeService.switch_trading_mode("live")

    if success:
        SettingsService.log_user_action(
            user_id, callback.from_user.username, "switched to LIVE mode"
        )
        await callback.message.edit_text(
            text=f"🔴 {message}\n\n{TradingModeService.get_mode_info()}",
            reply_markup=_get_trading_mode_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            text=f"❌ {message}\n\n{TradingModeService.get_mode_info()}",
            reply_markup=_get_trading_mode_keyboard(),
            parse_mode="Markdown"
        )


@trading_mode_router.callback_query(F.data == "settings_back", AuthState.unlocked)
async def process_trading_mode_back(callback: types.CallbackQuery, state: FSMContext):
    """Handle back button from trading mode menu - return to main settings menu."""
    from app.bot.keyboards.inline import get_settings_keyboard

    user_id = callback.from_user.id
    SettingsService.log_user_action(
        user_id, callback.from_user.username, "returned from trading mode menu"
    )

    # Get settings menu text
    api_status = "Connected"  # Default status
    settings_text = (
        f"**Settings Menu**\n\n"
        f"Telegram ID: {user_id}\n"
        f"API Status: {api_status}\n"
        f"Choose an option below:"
    )

    await callback.message.edit_text(
        text=settings_text,
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("Returned to settings.")


def _get_trading_mode_keyboard() -> types.InlineKeyboardMarkup:
    """Get trading mode selection keyboard."""
    buttons = [
        [
            types.InlineKeyboardButton(
                text="📦 Switch to Sandbox",
                callback_data="mode_switch_sandbox"
            ),
            types.InlineKeyboardButton(
                text="🔴 Switch to Live",
                callback_data="mode_switch_live"
            )
        ],
        [
            types.InlineKeyboardButton(
                text="🔙 Back to Settings",
                callback_data="settings_back"
            )
        ]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)
