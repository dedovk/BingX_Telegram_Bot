import dotenv
import pyotp

from aiogram.filters import StateFilter
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.states import AuthState, SettingsState
from app.bot.keyboards.inline import get_settings_keyboard, get_back_to_settings_keyboard
from app.bot.keyboards.reply import remove_menu
from app.bot.handlers.wallet import get_bingx_client
from app.core.security import encrypt_secret, hash_pin, verify_pin
from app.bingx.client import BingXClient
from app.core.config import settings

settings_router = Router()


def base_settings_menu(user_id) -> str:
    text = (
        f"**Settings Menu**\n\n"
        f"Telegram ID: {user_id}\n"
        f"API Status: Connected\n"
        f"Choose an option below:"
    )
    return text


@settings_router.message(F.text == "SETTINGS", AuthState.unlocked)
async def show_settings_menu(message: types.Message, state: FSMContext):
    """ """
    user_id = message.from_user.id

    logger.info(
        f"User(ID: {user_id}, Username: {message.from_user.username}) open settings menu.")

    await message.answer(
        text=base_settings_menu(user_id),
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
        f"**Settings Menu**\n\n"
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


@settings_router.callback_query(F.data == "settings_update_api", AuthState.unlocked)
async def process_update_api_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SettingsState.waiting_for_api_key)
    await state.update_data(prompt_msg_id=callback.message.message_id)

    logger.info(
        f"User(ID: {callback.from_user.id}, Username: {callback.from_user.username}) changing API keys.")

    await callback.message.edit_text(
        "**Update API keys**\n\n"
        "Please send your new API key\n"
        "*(You can cancel this action by pressing the button below)*",
        reply_markup=get_back_to_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@settings_router.message(SettingsState.waiting_for_api_key)
async def process_new_api_key(message: types.Message, state: FSMContext):
    """catch the new API key and asks to enter secret key"""

    new_api_key = message.text.strip()
    await state.update_data(new_api_key=new_api_key)

    await message.delete()

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")

    await state.set_state(SettingsState.waiting_for_secret_key)

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=prompt_msg_id,
        text=("**API key received** \n\n"
              "Now, please send me your new **Secret key**\n"
              "*(This message will be automatically deleted for security)*"
              ),
        reply_markup=get_back_to_settings_keyboard(),
        parse_mode="Markdown"
    )


@settings_router.message(SettingsState.waiting_for_secret_key)
async def process_new_secret_key(message: types.Message, state: FSMContext):
    """ """
    new_secret_key = message.text.strip()
    await message.delete()

    data = await state.get_data()
    new_api_key = data.get("new_api_key")
    prompt_msg_id = data.get("prompt_msg_id")

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=prompt_msg_id,
        text="*Verifying new API keys with BingX...*",
        parse_mode="Markdown")

    client = None
    try:
        client = BingXClient(api_key=new_api_key, secret_key=new_secret_key)
        await client.get_active_spot_balance()  # if keys are not valid, raising error

        encrypted_secret = encrypt_secret(
            new_secret_key, settings.ENCRYPTION_MASTER_KEY)

        dotenv.set_key(".env", "BINGX_API_KEY", new_api_key)
        dotenv.set_key(".env", "BINGX_SECRET_ENCRYPTED", encrypted_secret)

        settings.BINGX_API_KEY = new_api_key
        settings.BINGX_SECRET_ENCRYPTED = new_secret_key

        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_msg_id,
            text="**Success!** API Keys have been updated and securely saved.",
            parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Failed to update API keys: {e}")
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_msg_id,
            text=("**Connection Error**\n"
                  "The keys you provided are invalid or lack permissions. Please try again."),
            parse_mode="Markdown"
        )
    finally:
        if client:
            await client.close_connection()

        await state.set_state(AuthState.unlocked)
        await state.update_data(new_api_key=None)


@settings_router.callback_query(F.data == "settings_change_pin", AuthState.unlocked)
async def process_change_pin_start(callback: types.CallbackQuery, state: FSMContext):

    await state.set_state(SettingsState.waiting_for_old_pin)
    await state.update_data(prompt_msg_id=callback.message.message_id)

    logger.info(
        f"User(ID: {callback.from_user.id}, Username: {callback.from_user.username}) changing PIN.")

    await callback.message.edit_text(
        "**Change PIN code**\n\n"
        "For security reasons, please enter your **CURRENT PIN** first.\n\n"
        "*(You can cancel this action by pressing the button below)*",
        reply_markup=get_back_to_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@settings_router.message(SettingsState.waiting_for_old_pin)
async def process_old_pin(message: types.Message, state: FSMContext):

    entered_pin = message.text.strip()
    await message.delete()

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")

    is_valid = verify_pin(entered_pin, settings.PIN_HASH)

    if not is_valid:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_msg_id,
            text="**Access denied** \n Incorrect PIN code. Action cancelled.",
            reply_markup=get_back_to_settings_keyboard(),
            parse_mode="Markdown"
        )
        logger.warning(
            f"User(ID: {message.from_user.id}, Username: {message.from_user.username}), Incorrect PIN code. .")
        await state.set_state(AuthState.unlocked)
        return

    await state.set_state(SettingsState.waiting_for_new_pin)
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=prompt_msg_id,
        text="**Identity verified** \nNow, enter your **NEW PIN**\n",
        reply_markup=get_back_to_settings_keyboard(),
        parse_mode="Markdown",
    )


@settings_router.message(SettingsState.waiting_for_new_pin)
async def process_new_pin(message: types.Message, state: FSMContext):

    new_pin = message.text.strip()
    await message.delete()

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")

    if not new_pin.isdigit() or not (4 <= len(new_pin) <= 6):
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_msg_id,
            text="**Invalid format** \n Pin must contain only 4 to 6 numbers. Try again.",
            reply_markup=get_back_to_settings_keyboard(),
            parse_mode="Markdown"
        )
        return

    try:
        hashed_new_pin = hash_pin(new_pin)

        dotenv.set_key(".env", "PIN_HASH", hashed_new_pin)

        settings.PIN_HASH = hashed_new_pin

        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_msg_id,
            text="**Success!** \n Your PIN has been securely updated. \n Write it down in a safe place.",
            reply_markup=get_back_to_settings_keyboard(),
            parse_mode="Markdown"
        )
        logger.success(
            f"User(ID: {message.from_user.id}, Username: {message.from_user.username}) changed their PIN")
    except Exception as e:
        logger.error(
            f"User(ID: {message.from_user.id}, Username: {message.from_user.username}), Failed to save new PIN: {e}")
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_msg_id,
            text="**Error!** \n Could not save the new PIN.",
            parse_mode="Markdown"
        )
    finally:
        await state.set_state(AuthState.unlocked)


@settings_router.callback_query(
    F.data == "settings_back",
    StateFilter(
        SettingsState.waiting_for_api_key,
        SettingsState.waiting_for_secret_key,
        SettingsState.waiting_for_old_pin,
        SettingsState.waiting_for_new_pin,
        SettingsState.waiting_for_pin_for_2fa
    ))
async def process_settings_back(callback: types.CallbackQuery, state: FSMContext):
    """ """
    logger.info(
        f"User(ID: {callback.from_user.id}, Username: {callback.from_user.username}) cancel an action.")
    await state.set_state(AuthState.unlocked)
    user_id = callback.from_user.id
    text = base_settings_menu(user_id)

    await callback.message.edit_text(
        text=text,
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("Action cancelled.")
