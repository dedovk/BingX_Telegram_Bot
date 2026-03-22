from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_menu() -> ReplyKeyboardMarkup:
    """return main menu (only for auth)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="SPOT"), KeyboardButton(text='FUTURES')],
            [KeyboardButton(text="SETTINGS")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose ane action..."
    )


def remove_menu() -> ReplyKeyboardRemove:
    """remove main menu"""
    return ReplyKeyboardRemove()
