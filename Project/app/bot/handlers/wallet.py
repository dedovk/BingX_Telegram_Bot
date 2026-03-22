from aiogram import types, Router
from aiogram.filters import Command
from loguru import logger

from app.bot.states import AuthState
from app.core.config import settings
from app.core.security import decrypt_secret
from app.bingx.client import BingXClient

wallet_router = Router()


@wallet_router.message(Command("balance"), AuthState.unlocked)
async def cmd_balance(message: types.Message):

    msg = await message.answer("Obtaining data...")
    client = None
    try:
        clean_secret = decrypt_secret(
            settings.BINGX_SECRET_ENCRYPTED,
            settings.ENCRYPTION_MASTER_KEY
        )

        client = BingXClient(
            api_key=settings.BINGX_API_KEY,
            secret_key=clean_secret
        )

        usdt_balance = await client.get_usdt_balance()

        await msg.edit_text(f"<b>Your aviable balance:</b> {usdt_balance:.2f} USDT", parse_mode="HTML")

    except Exception as e:
        logger.exception(f"/balance command execution error: {e}")
        await msg.edit_text("Error when receiving balance. Check logs.")

    finally:
        if client:
            await client.close_connection()


@wallet_router.message(Command("balance"))
async def cmd_balance_locked(message: types.Message):
    await message.answer(" First unlock the bot /unlock")
