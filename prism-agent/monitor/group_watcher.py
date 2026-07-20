"""
Guruh monitoring — Telethon userbot (shaxsiy akkount orqali).

Barcha a'zo bo'lgan guruhlarni tinglaydi. Har bir xabarda ismingiz (variantlari
bilan) qidiriladi. Golos/video xabar bo'lsa — avval Whisper orqali matnga aylantiriladi.
Moslik topilsa: egaga (o'zingizga) darhol shaxsiy eslatma + Supabase'ga log.

XAVFSIZLIK: bu userbot FAQAT o'qish va eslatma uchun. Guruhlarga hech qanday
avtomatik xabar yuborilmaydi, spam qilinmaydi.
"""

import asyncio
import tempfile
from pathlib import Path

from core import config
from core.db import get_supabase
from core.logging_setup import get_logger
from core.notify import notify_owner
from core.transcribe import transcribe_file
from monitor.name_matcher import NameMatch, find_name

log = get_logger("group_watcher")


def build_link(chat, message_id: int) -> str | None:
    """Xabarga havola quradi (iloji bo'lsa). Umumiy guruhlar uchun username, aks holda /c/ formati."""
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{message_id}"
    chat_id = getattr(chat, "id", None)
    if chat_id:
        # Telethon'da supergroup/kanal id musbat bo'ladi; /c/ havolasi shu id bilan ishlaydi
        return f"https://t.me/c/{chat_id}/{message_id}"
    return None


def build_alert(
    chat_title: str,
    sender_name: str,
    kind: str,
    content: str,
    match: NameMatch,
    link: str | None,
) -> str:
    """Egaga yuboriladigan eslatma matnini shakllantiradi."""
    kind_label = {
        "text": "matn",
        "voice": "ovozli xabar",
        "video_note": "video xabar",
        "video": "video",
        "audio": "audio",
    }.get(kind, kind)

    lines = [
        "🔔 Sizni tilga olishdi!",
        f"Guruh: {chat_title}",
        f"Kim: {sender_name}",
        f"Tur: {kind_label} (moslik: {match.variant} ~{match.score:.0f}%)",
        "",
        f"Xabar:\n{content.strip()}",
    ]
    if link:
        lines.append("")
        lines.append(f"🔗 {link}")
    return "\n".join(lines)


def _sync_log_hit(row: dict) -> None:
    get_supabase().table(config.SUPABASE_MONITOR_TABLE).insert(row).execute()


async def log_hit(row: dict) -> None:
    """Topilmani Supabase monitor_hits jadvaliga yozadi."""
    try:
        await asyncio.to_thread(_sync_log_hit, row)
    except Exception:
        log.exception("Monitoring logini yozishda xato")


async def _extract_content(event) -> tuple[str, str]:
    """
    Xabardan (kind, content) qaytaradi. Matn bo'lsa to'g'ridan-to'g'ri, ovoz/video bo'lsa
    yuklab olib Whisper orqali transkript qiladi.
    """
    msg = event.message
    if getattr(msg, "voice", None):
        kind = "voice"
    elif getattr(msg, "video_note", None):
        kind = "video_note"
    elif getattr(msg, "video", None):
        kind = "video"
    elif getattr(msg, "audio", None):
        kind = "audio"
    else:
        return "text", event.raw_text or ""

    # Media xabar — vaqtinchalik faylga yuklab, transkript qilamiz
    with tempfile.TemporaryDirectory() as tmp:
        path = await event.download_media(file=str(Path(tmp) / "media"))
        if not path:
            return kind, ""
        transcript = await transcribe_file(path)
    return kind, transcript


async def process_event(event) -> None:
    """Bitta yangi xabarni qayta ishlaydi (ism qidiradi, topilsa eslatma + log)."""
    try:
        # Faqat guruh/kanal xabarlari
        if not (getattr(event, "is_group", False) or getattr(event, "is_channel", False)):
            return

        kind, content = await _extract_content(event)
        if not content:
            return

        match = find_name(content, config.MONITOR_NAME_VARIANTS)
        if match is None:
            return

        chat = await event.get_chat()
        sender = await event.get_sender()
        chat_title = getattr(chat, "title", None) or "Noma'lum guruh"
        sender_name = _display_name(sender)
        link = build_link(chat, event.message.id)

        log.info(
            "Moslik topildi: guruh=%r kim=%r variant=%s(%.0f)",
            chat_title, sender_name, match.variant, match.score,
        )

        # Egaga darhol eslatma
        alert = build_alert(chat_title, sender_name, kind, content, match, link)
        await notify_owner(alert)

        # Supabase'ga log
        await log_hit(
            {
                "chat_id": getattr(chat, "id", None),
                "chat_title": chat_title,
                "sender_id": getattr(sender, "id", None),
                "sender_name": sender_name,
                "message_id": event.message.id,
                "kind": kind,
                "content": content,
                "matched_variant": match.variant,
                "match_score": int(match.score),
                "message_link": link,
            }
        )
    except Exception:
        log.exception("Xabarni qayta ishlashda xato")


def _display_name(sender) -> str:
    """Yuboruvchi ismini chiroyli ko'rinishga keltiradi."""
    if sender is None:
        return "Noma'lum"
    first = getattr(sender, "first_name", "") or ""
    last = getattr(sender, "last_name", "") or ""
    username = getattr(sender, "username", None)
    name = (first + " " + last).strip()
    if name and username:
        return f"{name} (@{username})"
    if name:
        return name
    if username:
        return f"@{username}"
    return "Noma'lum"


async def main() -> None:
    """Telethon userbotni ishga tushiradi va guruhlarni tinglaydi."""
    from telethon import TelegramClient, events

    if not (config.TELEGRAM_API_ID and config.TELEGRAM_API_HASH):
        raise RuntimeError(
            "TELEGRAM_API_ID / TELEGRAM_API_HASH topilmadi. https://my.telegram.org dan oling."
        )
    if not config.MONITOR_NAME_VARIANTS:
        log.warning("MONITOR_NAME_VARIANTS bo'sh — hech qanday ism qidirilmaydi.")

    client = TelegramClient(
        config.TELETHON_SESSION_NAME, config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH
    )

    @client.on(events.NewMessage)
    async def _handler(event):  # noqa: ANN001
        await process_event(event)

    log.info("Guruh monitoring ishga tushmoqda (Telethon)...")
    await client.start()  # birinchi marta telefon/kod so'raydi, keyin sessiya saqlanadi
    log.info("Guruh monitoring aktiv. Ism variantlari: %s", config.MONITOR_NAME_VARIANTS)
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
