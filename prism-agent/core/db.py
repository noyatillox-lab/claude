"""
Umumiy Supabase klient — barcha tool/servislar shu yagona klientdan foydalanadi.
service_role kaliti bilan (server tomonda), dangasa yuklash (birinchi chaqiruvda).
"""

from core import config
from core.logging_setup import get_logger

log = get_logger("db")

_client = None


def get_supabase():
    """Supabase klientini qaytaradi (bir marta yaratilib keshlanadi)."""
    global _client
    if _client is None:
        from supabase import create_client

        if not (config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY):
            raise RuntimeError(
                "SUPABASE_URL yoki SUPABASE_SERVICE_KEY topilmadi. .env faylini to'ldiring."
            )
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
        log.info("Supabase klienti yaratildi.")
    return _client
