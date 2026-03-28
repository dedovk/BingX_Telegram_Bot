"""Security settings handlers - handles 2FA/TOTP management UI."""
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.states import AuthState, SettingsState
from app.bot.keyboards.inline import get_back_to_settings_keyboard
from app.bot.services import SecuritySettingsService, PINSettingsService

security_settings_router = Router()


@security_settings_router.callback_query(F.data == "settings_reset_2fa", AuthState.unlocked)
async def process_reset_2fa_start(callback: types.CallbackQuery, state: FSMContext):
    """Start 2FA reset process - request PIN for verification."""
    await state.set_state(SettingsState.waiting_for_pin_for_2fa)
    await state.update_data(prompt_msg_id=callback.message.message_id)

    logger.info(
        f"User(ID: {callback.from_user.id}, Username: {callback.from_user.username}) initiated 2FA reset."
    )

    await callback.message.edit_text(
        "**Reset 2FA**\n\n"
        "To reset your Two-Factor Authentication, please enter your **PIN code** first to verify your identity.\n\n"
        "*(You can cancel this action by pressing the button below)*",
        reply_markup=get_back_to_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@security_settings_router.message(SettingsState.waiting_for_pin_for_2fa)
async def process_pin_for_2fa(message: types.Message, state: FSMContext):
    """Verify PIN and proceed with 2FA reset."""
    entered_pin = message.text.strip()
    await message.delete()

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    user_id = message.from_user.id

    # Verify PIN
    is_valid = PINSettingsService.verify_current_pin(entered_pin)

    if not is_valid:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_msg_id,
            text="**Access denied** \n Incorrect PIN code. Action cancelled.",
            reply_markup=get_back_to_settings_keyboard(),
            parse_mode="Markdown"
        )
        PINSettingsService.log_user_warning(
            user_id, message.from_user.username, "entered incorrect PIN code during 2FA reset"
        )
        await state.clear()
        await state.set_state(AuthState.unlocked)
        return

    # Reset 2FA
    success, error_msg, new_secret = SecuritySettingsService.reset_2fa()

    if success:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_msg_id,
            text=(
                "**2FA Reset Successful**\n\n"
                "Please add the following **Setup Key** to your Authenticator app (Google Authenticator, Authy, etc.):\n\n"
                f"`{new_secret}`\n\n"
                "*(Tap the key above to copy it)*\n\n"
                "⚠️ **Important:** Do not lose this key! You will need it to unlock the bot."
            ),
            reply_markup=get_back_to_settings_keyboard(),
            parse_mode="Markdown"
        )
        SecuritySettingsService.log_user_success(
            user_id, message.from_user.username, "reset 2FA secret"
        )
    else:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_msg_id,
            text=f"**Error!** \n {error_msg}",
            reply_markup=get_back_to_settings_keyboard(),
            parse_mode="Markdown"
        )
        SecuritySettingsService.log_user_error(
            user_id, message.from_user.username, "failed to reset 2FA")

    await state.clear()
    await state.set_state(AuthState.unlocked)
