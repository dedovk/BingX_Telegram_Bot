import asyncio

from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from loguru import logger

from app.core.config import settings
from app.core.security import verify_pin

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

router = Router()


class AuthState(StatesGroup):
    waiting_for_pin = State()  # bot waiting for entered PIN
    unlocked = State()  # bot unlocked and ready to work


@router.message(Command("unlock"))
async def cmd_unlock(message: types.Message, state: FSMContext):
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
            f"User(ID: {message.from_user.id}, Username: {message.from_user.username}) successfully unblocked the bot")
        await message.answer("PIN code accept. Access is open.")
        # put into unblocked state
        await state.set_state(AuthState.unlocked)
    else:
        logger.warning(
            f"Wrong PIN code from User(ID: {message.from_user.id}, Username: {message.from_user.username})")
        await message.answer("Wrong PIN code. Try again or click /cancel")
        # dont change the state, bot still waiting for PIN


@router.message(Command("lock"))
async def cmd_lock(message: types.Message, state: FSMContext):
    """command for forced lock(logout)"""
    await state.clear()  # clear the states
    await message.answer("Session locked.")

dp.include_router(router)


async def main():
    logger.info("Bot is running.")

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot is stopped manually.")
