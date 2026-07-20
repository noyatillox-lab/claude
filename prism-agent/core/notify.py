"""
Egaga (o'zingizga) shaxsiy xabar yuborish — aiogram bot orqali.
Guruh monitoring moslik topganda shu funksiya orqali darhol eslatma keladi.
"""

from aiogram import Bot

from core import config
from core.logging_setup import get_logger

log = get_logger("notify")

_bot: Bot | None = None


def _get_bot() -> Bot:
    global _bot
    if _bot is None:
        if not config.TELEGRAM_BOT_TOKEN:
            raise RuntimeError("TELEGRAM_BOT_TOKEN topilmadi. .env faylini to'ldiring.")
        _bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    return _bot


async def notify_owner(text: str) -> None:
    """Egaga (TELEGRAM_OWNER_CHAT_ID) matnli eslatma yuboradi."""
    if not config.TELEGRAM_OWNER_CHAT_ID:
        log.warning("TELEGRAM_OWNER_CHAT_ID sozlanmagan — eslatma yuborilmadi.")
        return
    try:
        await _get_bot().send_message(
            config.TELEGRAM_OWNER_CHAT_ID, text, disable_web_page_preview=True
        )
    except Exception:
        log.exception("Egaga eslatma yuborishda xato")


async def close() -> None:
    """Bot sessiyasini yopadi (dastur to'xtaganda)."""
    global _bot
    if _bot is not None:
        await _bot.session.close()
        _bot = None
