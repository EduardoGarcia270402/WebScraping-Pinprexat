from __future__ import annotations

import asyncio

from config.settings import get_settings


def send_telegram(message: str) -> bool:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False

    async def _send() -> None:
        from telegram import Bot

        bot = Bot(token=settings.telegram_bot_token or "")
        await bot.send_message(chat_id=settings.telegram_chat_id, text=message)

    asyncio.run(_send())
    return True
