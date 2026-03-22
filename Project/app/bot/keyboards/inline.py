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
