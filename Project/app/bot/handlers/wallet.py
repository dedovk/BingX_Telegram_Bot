from aiogram import types, Router, F
from aiogram.types import CallbackQuery
from datetime import datetime
from loguru import logger

from app.bot.states import AuthState
from app.core.config import settings
from app.core.security import decrypt_secret
from app.bingx.factory import BingXClientFactory

from app.bot.keyboards.reply import remove_menu
from app.bot.keyboards.inline import get_refresh_keyboard

wallet_router = Router()


def get_bingx_client():
    """Get BingX client - uses factory to support live/sandbox modes."""
    return BingXClientFactory.create()


def generate_spot_portfolio_text(balances: list) -> str:
    if not balances:
        return "<b>Your Spot portfolio is empty. </b>"

    text = "<b>Your Spot portfolio: </b> \n\n"
    for item in balances:
        text += f"{item.asset}: {item.total:.6f} \n"
        if item.locked > 0:
            text += f"<i>(In orders: {item.locked:.6f})</i>"
    return text

# futures balanace


@wallet_router.message(F.text == "FUTURES", AuthState.unlocked)
async def cmd_balance(message: types.Message):

    msg = await message.answer("Obtaining data...")
    client = None
    try:
        client = get_bingx_client()

        usdt_balance = await client.get_usdt_balance()

        await msg.edit_text(f"<b>Your available balance:</b> {usdt_balance:.2f} USDT", parse_mode="HTML")

    except Exception as e:
        logger.exception(f"/balance command execution error: {e}")
        await msg.edit_text("Error when receiving balance. Check logs.")

    finally:
        if client:
            await client.close_connection()


@wallet_router.message(F.text == "FUTURES")
async def cmd_balance_locked(message: types.Message):
    await message.answer(" First unlock the bot /unlock")

# spot portfolio


@wallet_router.message(F.text == "SPOT", AuthState.unlocked)
async def handle_spot_portfolio(message: types.Message):

    msg = await message.answer("Obtaining data...")
    client = None

    try:
        client = get_bingx_client()

        balances = await client.get_active_spot_balance()

        text = generate_spot_portfolio_text(balances)

        await msg.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_refresh_keyboard("SPOT")
        )
    except Exception as e:
        logger.exception(f"Spot portfolio execution error: {e}")
        await msg.edit_text("Error when receiving Spot balance. Check logs.")

    finally:
        if client:
            await client.close_connection()


@wallet_router.message(F.text == "SPOT")
async def handle_spot_portfolio_locked(message: types.Message):
    await message.answer(" First unlock the bot /unlock", reply_markup=remove_menu())

# inline-buttons(refresh)


@wallet_router.callback_query(F.data == "refresh_SPOT", AuthState.unlocked)
async def process_refresh_spot(callback: CallbackQuery):
    await callback.answer("Refreshing balance ...", show_alert=False)

    client = None
    try:
        client = get_bingx_client()

        balances = await client.get_active_spot_balance()

        text = generate_spot_portfolio_text(balances)

        current_time = datetime.now().strftime("%H:%M:%S")
        text += f"\n<i>Refreshed: {current_time}</i>"

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_refresh_keyboard("SPOT")
        )
    except Exception as e:
        logger.exception(f"Spot refresh error: {e}")
        await callback.answer("Refreshing error. Check your logs.", show_alert=True)

    finally:
        if client:
            await client.close_connection()

# fallback


@wallet_router.callback_query(F.data.startswith("refresh_"))
async def process_refresh_locked(callback: CallbackQuery):
    await callback.answer("Bot blocked. Enter /unlock", show_alert=True)
