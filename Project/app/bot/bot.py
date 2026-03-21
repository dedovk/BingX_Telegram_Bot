import asyncio

from aiogram import Bot, Dispatcher
from loguru import logger

from app.core.config import settings
from app.bot.middleware.auth import IDAuthMiddleware
# import routers
from app.bot.handlers.base import base_router
from app.bot.handlers.wallet import wallet_router

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

dp.include_routers(
    base_router,
    wallet_router
)


async def main():
    logger.info("Bot is running.")
    dp.message.middleware(IDAuthMiddleware())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot is stopped manually.")
