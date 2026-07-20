"""
Ovoz/video -> matn (transkript) — OpenAI Whisper API orqali.
Guruh monitoring golos/video xabarlarni shu funksiya orqali matnga aylantiradi.
"""

import asyncio

from core import config
from core.logging_setup import get_logger

log = get_logger("transcribe")

_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI

        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY topilmadi. .env faylini to'ldiring.")
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


def _sync_transcribe(file_path: str) -> str:
    with open(file_path, "rb") as f:
        resp = _get_client().audio.transcriptions.create(
            model=config.WHISPER_MODEL, file=f
        )
    return (resp.text or "").strip()


async def transcribe_file(file_path: str) -> str:
    """Audio/video faylni matnga aylantiradi (event loop'ni bloklamaydi)."""
    try:
        text = await asyncio.to_thread(_sync_transcribe, file_path)
        log.info("Transkript tayyor (%d belgi): %s", len(text), file_path)
        return text
    except Exception:
        log.exception("Transkriptsiyada xato: %s", file_path)
        return ""
