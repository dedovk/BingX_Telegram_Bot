from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from loguru import logger

from app.core.config import settings


class IDAuthMiddleware(BaseMiddleware):
    """ """

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id

        if user_id not in settings.ALLOWED_USERS_IDS:
            logger.warning(
                f"Access attempt. ID: {user_id}, Username: @{event.from_user.username}")

            await event.answer("Access denied. You are not able to use this bot")
            return
        return await handler(event, data)
