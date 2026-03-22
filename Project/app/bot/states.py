from aiogram.fsm.state import StatesGroup, State


class AuthState(StatesGroup):
    waiting_for_pin = State()  # bot waiting for enter PIN
    waiting_for_totp = State()  # bot waiting for enter TOTP code
    unlocked = State()  # bot unlocked and ready to work


class SettingsState(StatesGroup):
    waiting_for_api_key = State()  # bot waiting for enter api key
    waiting_for_secret_key = State()  # bot waiting for enter secret key
