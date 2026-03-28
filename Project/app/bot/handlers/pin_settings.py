"""PIN settings handlers - handles PIN management UI."""
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.states import AuthState, SettingsState
from app.bot.keyboards.inline import get_back_to_settings_keyboard
from app.bot.services import PINSettingsService

pin_settings_router = Router()


@pin_settings_router.callback_query(F.data == "settings_change_pin", AuthState.unlocked)
async def process_change_pin_start(callback: types.CallbackQuery, state: FSMContext):
    """Start PIN change process - request current PIN."""
    await state.set_state(SettingsState.waiting_for_old_pin)
    await state.update_data(prompt_msg_id=callback.message.message_id)

    logger.info(
        f"User(ID: {callback.from_user.id}, Username: {callback.from_user.username}) changing PIN."
    )

    await callback.message.edit_text(
        "**Change PIN code**\n\n"
        "For security reasons, please enter your **CURRENT PIN** first.\n\n"
        "*(You can cancel this action by pressing the button below)*",
        reply_markup=get_back_to_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@pin_settings_router.message(SettingsState.waiting_for_old_pin)
async def process_old_pin(message: types.Message, state: FSMContext):
    """Verify current PIN and proceed if valid."""
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
            user_id, message.from_user.username, "entered incorrect PIN code"
        )
        await state.clear()
        await state.set_state(AuthState.unlocked)
        return

    # Move to new PIN entry
    await state.set_state(SettingsState.waiting_for_new_pin)
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=prompt_msg_id,
        text="**Identity verified** \nNow, enter your **NEW PIN**\n",
        reply_markup=get_back_to_settings_keyboard(),
        parse_mode="Markdown",
    )


@pin_settings_router.message(SettingsState.waiting_for_new_pin)
async def process_new_pin(message: types.Message, state: FSMContext):
    """Validate new PIN format and save if valid."""
    new_pin = message.text.strip()
    await message.delete()

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    user_id = message.from_user.id

    # Validate format
    is_valid, error_msg = PINSettingsService.validate_pin_format(new_pin)
    if not is_valid:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=prompt_msg_id,
            text=f"**Invalid format** \n {error_msg} Try again.",
            reply_markup=get_back_to_settings_keyboard(),
            parse_mode="Markdown"
        )
        return

    # Try to update PIN
    success, result_message = PINSettingsService.update_pin(new_pin)

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=prompt_msg_id,
        text=f"**{'Success!' if success else 'Error!'}** \n {result_message}",
        reply_markup=get_back_to_settings_keyboard(),
        parse_mode="Markdown"
    )

    if success:
        PINSettingsService.log_user_success(
            user_id, message.from_user.username, "changed PIN")
    else:
        PINSettingsService.log_user_error(
            user_id, message.from_user.username, "failed to change PIN")

    await state.clear()
    await state.set_state(AuthState.unlocked)
