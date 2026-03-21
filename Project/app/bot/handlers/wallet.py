from aiogram import types, Router
from aiogram.filters import Command
from loguru import logger

from app.bot.states import AuthState

wallet_router = Router()


@wallet_router.message(Command("balance"), AuthState.unlocked)
async def cmd_balance(message: types.Message):
    # Поки що заглушка, сюди ми додамо виклик BingXClient
    await message.answer(" Твій баланс: 100500 USDT (Заглушка)")


@wallet_router.message(Command("balance"))
async def cmd_balance_locked(message: types.Message):
    await message.answer(" First unlock the bot /unlock")
