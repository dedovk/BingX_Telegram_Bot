from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_refresh_keyboard(target: str) -> InlineKeyboardMarkup:
    """ """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Refresh",
        callback_data=f"refresh_{target}"
    )
    return builder.as_markup()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """ """
    builder = InlineKeyboardBuilder()

    builder.button(text="Update API keys", callback_data="settings_update_api")
    builder.button(text="Check API status", callback_data="settings_check_api")
    builder.button(text="Trading Mode", callback_data="settings_trading_mode")
    builder.button(text="Change PIN", callback_data="settings_change_pin")
    builder.button(text="Reset 2FA", callback_data="settings_reset_2fa")
    builder.button(text="Lock bot", callback_data="settings_lock")

    builder.adjust(1, 1, 1, 2, 1)

    return builder.as_markup()


def get_back_to_settings_keyboard() -> InlineKeyboardMarkup:
    """ """
    builder = InlineKeyboardBuilder()
    builder.button(text="Back to Settings", callback_data="settings_back")
    return builder.as_markup()
