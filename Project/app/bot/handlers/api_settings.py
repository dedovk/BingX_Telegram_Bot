"""API settings handlers - handles API key management UI."""
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.states import AuthState, SettingsState
from app.bot.keyboards.inline import get_back_to_settings_keyboard, get_settings_keyboard
from app.bot.services import APISettingsService

api_settings_router = Router()


@api_settings_router.callback_query(F.data == "settings_check_api", AuthState.unlocked)
async def process_settings_check_api(callback: types.CallbackQuery):
    """Check and display current API connection status."""
    user_id = callback.from_user.id
    logger.info(
        f"User(ID: {callback.from_user.id}, Username: {callback.from_user.username}) checking API."
    )

    # Show checking status
    await callback.message.edit_text(
        text=_format_settings_menu(
            user_id, api_status="Checking Connection..."),
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )

    # Check connection
    is_valid, status_text = await APISettingsService.check_api_connection()

    # Update with result
    await callback.message.edit_text(
        text=_format_settings_menu(user_id, api_status=status_text),
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("API status updated.")


@api_settings_router.callback_query(F.data == "settings_update_api", AuthState.unlocked)
async def process_update_api_start(callback: types.CallbackQuery, state: FSMContext):
    """Start API key update process."""
    await state.set_state(SettingsState.waiting_for_api_key)
    await state.update_data(prompt_msg_id=callback.message.message_id)

    logger.info(
        f"User(ID: {callback.from_user.id}, Username: {callback.from_user.username}) changing API keys."
    )

    await callback.message.edit_text(
        "**Update API keys**\n\n"
        "Please send your new API key\n"
        "*(You can cancel this action by pressing the button below)*",
        reply_markup=get_back_to_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@api_settings_router.message(SettingsState.waiting_for_api_key)
async def process_new_api_key(message: types.Message, state: FSMContext):
    """Capture new API key and request secret key."""
    new_api_key = message.text.strip()
    await state.update_data(new_api_key=new_api_key)
    await message.delete()

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")

    await state.set_state(SettingsState.waiting_for_secret_key)

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=prompt_msg_id,
        text=(
            "**API key received** \n\n"
            "Now, please send me your new **Secret key**\n"
            "*(This message will be automatically deleted for security)*"
        ),
        reply_markup=get_back_to_settings_keyboard(),
        parse_mode="Markdown"
    )


@api_settings_router.message(SettingsState.waiting_for_secret_key)
async def process_new_secret_key(message: types.Message, state: FSMContext):
    """Capture secret key, validate both keys, and update configuration."""
    new_secret_key = message.text.strip()
    await message.delete()

    data = await state.get_data()
    new_api_key = data.get("new_api_key")
    prompt_msg_id = data.get("prompt_msg_id")
    user_id = message.from_user.id

    # Show verifying status
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=prompt_msg_id,
        text="*Verifying new API keys with BingX...*",
        parse_mode="Markdown"
    )

    # Validate and update
    success, result_message = await APISettingsService.validate_and_update_api_keys(
        new_api_key, new_secret_key
    )

    # Show result
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=prompt_msg_id,
        text=f"**{('Success!' if success else 'Connection Error')}** \n {result_message}",
        reply_markup=get_back_to_settings_keyboard(),
        parse_mode="Markdown"
    )

    if success:
        APISettingsService.log_user_action(
            user_id, message.from_user.username, "updated API keys")
    else:
        APISettingsService.log_user_error(
            user_id, message.from_user.username, "failed to update API keys")

    await state.clear()
    await state.set_state(AuthState.unlocked)


def _format_settings_menu(user_id: int, api_status: str = "Connected") -> str:
    """Format settings menu text."""
    return (
        f"**Settings Menu**\n\n"
        f"Telegram ID: {user_id}\n"
        f"API Status: {api_status}\n"
        f"Choose an option below:"
    )
