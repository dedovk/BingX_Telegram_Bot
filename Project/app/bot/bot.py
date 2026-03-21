import asyncio

from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from loguru import logger

from app.core.config import settings
from app.core.security import verify_pin, verify_totp
from app.bot.middleware.auth import IDAuthMiddleware

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

router = Router()


class AuthState(StatesGroup):
    waiting_for_pin = State()  # bot waiting for enter PIN
    waiting_for_totp = State()  # bot waiting for enter TOTP code
    unlocked = State()  # bot unlocked and ready to work


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """command for cancel auth state"""
    current_state = await state.get_state()
    if current_state is None:
        return
    logger.info(
        f"User(ID: {message.from_user.id}, Username: {message.from_user.username}) cancelled auth process.")
    await state.clear()
    await message.answer("Authorization cancelled.")


@router.message(Command("unlock"))
async def cmd_unlock(message: types.Message, state: FSMContext):
    logger.info(
        f"User(ID: {message.from_user.id}, Username: {message.from_user.username}) trying to unlock the bot")
    """command for start unlocking"""
    await message.answer("Bot blocked. Enter PIN:")
    # transfer the user to the PIN code waiting time
    await state.set_state(AuthState.waiting_for_pin)


@router.message(AuthState.waiting_for_pin)
async def process_pin(message: types.Message, state: FSMContext):
    """this handler only catches the message that the user enters after /unlock"""
    user_pin = message.text

    is_valid = verify_pin(user_pin, settings.PIN_HASH)

    try:  # trying to delete user message with PIN code
        await message.delete()
    except Exception as e:
        logger.error(f"Failed to delete message with PIN code: {e}")

    if is_valid:
        logger.info(
            f"User(ID: {message.from_user.id}, Username: {message.from_user.username}) enter the correct pin ")
        await message.answer("PIN code accept. Enter a 6-digit code from Microsoft Authenticator: ")
        await state.set_state(AuthState.waiting_for_totp)
        # put into waiting_for_totp state
    else:
        logger.warning(
            f"Wrong PIN code from User(ID: {message.from_user.id}, Username: {message.from_user.username})")
        await message.answer("Wrong PIN code. Try again or click /cancel")
        # dont change the state, bot still waiting for PIN


@router.message(AuthState.waiting_for_totp)
async def process_totp(message: types.Message, state: FSMContext):
    user_code = message.text.replace(" ", "")
    is_valid = verify_totp(settings.TOTP_SECRET, user_code)

    try:
        await message.delete()
    except Exception as e:
        logger.error(f"Failed to delete message with TOTP code: {e}")

    if is_valid:
        logger.info(
            f"User(ID: {message.from_user.id}, Username: {message.from_user.username}) passed 2FA.")
        await message.answer("2FA passed.")
        await state.set_state(AuthState.unlocked)
    else:
        logger.warning(
            f"User(ID: {message.from_user.id}, Username: {message.from_user.username}) enter wrong TOTP code.")
        await message.answer("Wrong 2FA code. Try again or click /cancel")


@router.message(Command("lock"))
async def cmd_lock(message: types.Message, state: FSMContext):
    """command for forced lock(logout)"""
    await state.clear()  # clear the states
    await message.answer("Session locked.")

dp.include_router(router)


async def main():
    logger.info("Bot is running.")
    dp.message.middleware(IDAuthMiddleware())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot is stopped manually.")
