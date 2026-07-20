"""
Markazlashgan konfiguratsiya — barcha API kalitlar va sozlamalar shu yerdan o'qiladi.
Kod hech qayerda kalitni hardcode qilmaydi; hammasi .env orqali keladi.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# .env faylini prism-agent/ ildizidan yuklaymiz
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _get(name: str, default: str | None = None, required: bool = False) -> str | None:
    """Muhit o'zgaruvchisini o'qiydi. required=True bo'lsa va bo'sh bo'lsa — xato."""
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(
            f"Muhit o'zgaruvchisi topilmadi: {name}. "
            f".env faylida shu qiymatni to'ldiring (namuna: .env.example)."
        )
    return value


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_id_list(name: str) -> list[int]:
    """Vergul bilan ajratilgan ID'lar ro'yxatini butun sonlarga aylantiradi."""
    raw = os.getenv(name, "") or ""
    ids: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if part:
            try:
                ids.append(int(part))
            except ValueError:
                pass
    return ids


def _get_str_list(name: str) -> list[str]:
    raw = os.getenv(name, "") or ""
    return [p.strip() for p in raw.split(",") if p.strip()]


PROJECT_ROOT = _PROJECT_ROOT
LOGS_DIR = _PROJECT_ROOT / "logs"

# --- Anthropic (Claude) ---
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = _get("CLAUDE_MODEL", "claude-opus-4-8")
CLAUDE_MAX_TOKENS = _get_int("CLAUDE_MAX_TOKENS", 4096)

# --- OpenAI ---
OPENAI_API_KEY = _get("OPENAI_API_KEY")
EMBEDDING_MODEL = _get("EMBEDDING_MODEL", "text-embedding-3-small")
WHISPER_MODEL = _get("WHISPER_MODEL", "whisper-1")

# --- Telegram bot ---
TELEGRAM_BOT_TOKEN = _get("TELEGRAM_BOT_TOKEN")
TELEGRAM_ALLOWED_USER_IDS = _get_id_list("TELEGRAM_ALLOWED_USER_IDS")
TELEGRAM_OWNER_CHAT_ID = _get_int("TELEGRAM_OWNER_CHAT_ID", 0)

# --- Telethon userbot ---
TELEGRAM_API_ID = _get_int("TELEGRAM_API_ID", 0)
TELEGRAM_API_HASH = _get("TELEGRAM_API_HASH")
TELETHON_SESSION_NAME = _get("TELETHON_SESSION_NAME", "prism_userbot")

# --- Supabase ---
SUPABASE_URL = _get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = _get("SUPABASE_SERVICE_KEY")
# Vazifalar jadvali nomi (o'zingiznikiga moslashtirish uchun .env orqali o'zgartiriladi)
SUPABASE_TASKS_TABLE = _get("SUPABASE_TASKS_TABLE", "tasks")
# Guruh monitoring loglari jadvali (Bosqich 6)
SUPABASE_MONITOR_TABLE = _get("SUPABASE_MONITOR_TABLE", "monitor_hits")

# --- Replicate ---
REPLICATE_API_TOKEN = _get("REPLICATE_API_TOKEN")
REPLICATE_IMAGE_MODEL = _get("REPLICATE_IMAGE_MODEL", "black-forest-labs/flux-1.1-pro")

# --- Obsidian RAG ---
OBSIDIAN_VAULT_PATH = _get("OBSIDIAN_VAULT_PATH")
# 02_obsidian_rag_sync.py faylining yo'li (query_knowledge_base shu yerdan import qilinadi).
# Default: repo ildizidagi 02_obsidian_rag_sync.py (prism-agent'ning bir pog'ona tepasida).
OBSIDIAN_RAG_MODULE_PATH = _get(
    "OBSIDIAN_RAG_MODULE_PATH",
    str((_PROJECT_ROOT.parent / "02_obsidian_rag_sync.py")),
)

# --- Monitoring ---
MONITOR_NAME_VARIANTS = _get_str_list("MONITOR_NAME_VARIANTS")
