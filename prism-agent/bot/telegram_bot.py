"""
Telegram bot — aiogram, long polling rejimida (webhook YO'Q).

Har bir kelgan matn xabar orkestratorga uzatiladi, javob foydalanuvchiga qaytadi.
Xavfsizlik: faqat TELEGRAM_ALLOWED_USER_IDS ro'yxatidagi foydalanuvchilar yoza oladi.
Suhbat tarixi har bir foydalanuvchi uchun alohida (xotira Bosqich F'da Supabase'ga ko'chadi).
"""

import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from core import config
from core.logging_setup import get_logger
from core.orchestrator import AgentResult, Orchestrator

log = get_logger("bot")

# Har bir foydalanuvchi uchun suhbat tarixi: user_id -> messages ro'yxati
# (Bosqich F: bu xotira Supabase'ga ko'chiriladi; hozircha xotirada saqlanadi)
_HISTORY: dict[int, list[dict]] = {}

# Tarix cheksiz o'smasligi uchun oxirgi shuncha xabarni saqlaymiz
_MAX_HISTORY_MESSAGES = 30


def _is_allowed(user_id: int | None) -> bool:
    """Faqat ruxsat etilgan foydalanuvchilar botdan foydalana oladi."""
    if not config.TELEGRAM_ALLOWED_USER_IDS:
        # Ro'yxat bo'sh bo'lsa — hech kimga ruxsat yo'q (xavfsiz default)
        return False
    return user_id in config.TELEGRAM_ALLOWED_USER_IDS


def _trim_history(history: list[dict]) -> list[dict]:
    """Tarixni oxirgi _MAX_HISTORY_MESSAGES ta xabar bilan cheklaydi."""
    if len(history) <= _MAX_HISTORY_MESSAGES:
        return history
    return history[-_MAX_HISTORY_MESSAGES:]


async def process_text(orchestrator: Orchestrator, user_id: int, text: str) -> AgentResult:
    """
    Bitta matnli so'rovni qayta ishlaydi: tarixni oladi, orkestratorni chaqiradi,
    yangilangan tarixni saqlaydi. (Handler'lardan ajratilgan — test qilish oson.)
    """
    history = _HISTORY.get(user_id, [])
    result = await orchestrator.run(text, history=history, user_id=user_id)
    _HISTORY[user_id] = _trim_history(result.history)
    return result


def build_dispatcher(orchestrator: Orchestrator) -> Dispatcher:
    """Handler'larni ro'yxatga oluvchi Dispatcher yaratadi."""
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: Message) -> None:
        if not _is_allowed(message.from_user.id):
            await message.answer("Kechirasiz, sizga ruxsat berilmagan.")
            return
        await message.answer(
            "Salom! Men Prism AI assistentiman. 🤖\n"
            "Savol bering, vazifa qo'ying yoki rasm so'rang — yordam beraman.\n"
            "Suhbatni tozalash uchun /reset."
        )

    @dp.message(Command("reset"))
    async def cmd_reset(message: Message) -> None:
        if not _is_allowed(message.from_user.id):
            return
        _HISTORY.pop(message.from_user.id, None)
        await message.answer("Suhbat tarixi tozalandi. ✅")

    @dp.message(F.text)
    async def on_text(message: Message) -> None:
        user_id = message.from_user.id
        if not _is_allowed(user_id):
            await message.answer("Kechirasiz, sizga ruxsat berilmagan.")
            log.warning("Ruxsatsiz foydalanuvchi urinishi: %s", user_id)
            return

        log.info("Xabar (user=%s): %s", user_id, message.text[:120])
        # "Yozmoqda..." holatini ko'rsatamiz
        await message.bot.send_chat_action(message.chat.id, "typing")
        try:
            result = await process_text(orchestrator, user_id, message.text)
        except Exception:
            log.exception("Orkestrator xatosi (user=%s)", user_id)
            await message.answer(
                "Kechirasiz, texnik xatolik yuz berdi. Birozdan keyin qayta urinib ko'ring."
            )
            return

        # Matnli javob
        if result.text:
            await message.answer(result.text)
        # Generatsiya qilingan rasmlar bo'lsa — ularni yuboramiz
        for url in result.image_urls:
            try:
                await message.answer_photo(url)
            except Exception:
                log.exception("Rasm yuborishda xato: %s", url)
                await message.answer(f"Rasm: {url}")

    # Ovoz/video xabarlar — to'liq qo'llab-quvvatlash Whisper bilan (Bosqich 6)
    @dp.message(F.voice | F.video_note | F.video | F.audio)
    async def on_media(message: Message) -> None:
        if not _is_allowed(message.from_user.id):
            return
        await message.answer(
            "Ovoz/video transkripsiyasi keyingi bosqichda (Whisper) ulanadi."
        )

    return dp


async def main() -> None:
    """Botni long polling rejimida ishga tushiradi."""
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN topilmadi. .env faylini to'ldiring.")

    orchestrator = Orchestrator()
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    dp = build_dispatcher(orchestrator)

    log.info("Prism bot ishga tushdi (long polling).")
    # Eski navbatdagi update'larni tashlab, faqat yangilarini olamiz
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
