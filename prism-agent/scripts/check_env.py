"""
Ulanish tekshiruvi (doctor) — .env to'g'ri to'ldirilganini va OpenAI + Supabase
ishlashini tekshiradi. Obsidian sync'dan OLDIN ishga tushiring:
    python scripts/check_env.py
"""

import sys
from pathlib import Path

# prism-agent ildizini import yo'liga qo'shamiz
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import config  # noqa: E402

OK = "\033[92m✅\033[0m"
BAD = "\033[91m❌\033[0m"


def check_env_vars() -> bool:
    """Obsidian sync uchun zarur o'zgaruvchilar to'ldirilganmi."""
    required = {
        "OPENAI_API_KEY": config.OPENAI_API_KEY,
        "SUPABASE_URL": config.SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": config.SUPABASE_SERVICE_KEY,
        "OBSIDIAN_VAULT_PATH": config.OBSIDIAN_VAULT_PATH,
    }
    all_ok = True
    for name, value in required.items():
        if value and str(value).strip() and not str(value).startswith(("sk-xxx", "https://xxxxx")):
            print(f"  {OK} {name} to'ldirilgan")
        else:
            print(f"  {BAD} {name} bo'sh yoki namunaviy — .env da to'ldiring")
            all_ok = False
    return all_ok


def check_vault() -> bool:
    """Obsidian vault papkasi mavjud va ichida .md fayllar bormi."""
    path = Path(config.OBSIDIAN_VAULT_PATH or "")
    if not path.exists():
        print(f"  {BAD} Vault topilmadi: {path} — OBSIDIAN_VAULT_PATH ni tekshiring")
        return False
    md_count = sum(1 for _ in path.rglob("*.md"))
    if md_count == 0:
        print(f"  {BAD} Vault'da .md fayl topilmadi: {path}")
        return False
    print(f"  {OK} Vault topildi: {path} ({md_count} ta .md fayl)")
    return True


def check_openai() -> bool:
    """OpenAI kaliti ishlaydimi — kichik embedding chaqiruvi bilan."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=config.OPENAI_API_KEY)
        resp = client.embeddings.create(model=config.EMBEDDING_MODEL, input="test")
        dim = len(resp.data[0].embedding)
        print(f"  {OK} OpenAI ishlayapti (embedding o'lchovi: {dim})")
        return True
    except Exception as exc:
        print(f"  {BAD} OpenAI xatosi: {exc}")
        return False


def check_supabase() -> bool:
    """Supabase ulanadimi va obsidian_chunks jadvali mavjudmi."""
    try:
        from core.db import get_supabase

        supa = get_supabase()
        supa.table("obsidian_chunks").select("id").limit(1).execute()
        print(f"  {OK} Supabase ulandi va 'obsidian_chunks' jadvali mavjud")
        return True
    except Exception as exc:
        msg = str(exc)
        if "obsidian_chunks" in msg or "relation" in msg or "does not exist" in msg:
            print(f"  {BAD} 'obsidian_chunks' jadvali yo'q — 01_supabase_schema.sql ni "
                  "Supabase SQL Editor'da ishga tushiring")
        else:
            print(f"  {BAD} Supabase xatosi: {exc}")
        return False


def main() -> int:
    print("== Prism ulanish tekshiruvi ==\n")
    print("[1/4] .env o'zgaruvchilari:")
    env_ok = check_env_vars()
    print("\n[2/4] Obsidian vault:")
    vault_ok = check_vault() if env_ok else False
    print("\n[3/4] OpenAI:")
    openai_ok = check_openai() if env_ok else False
    print("\n[4/4] Supabase:")
    supa_ok = check_supabase() if env_ok else False

    print("\n" + "=" * 40)
    if env_ok and vault_ok and openai_ok and supa_ok:
        print(f"{OK} Hammasi tayyor! Endi sync qilsangiz bo'ladi.")
        return 0
    print(f"{BAD} Yuqoridagi ❌ larni tuzatib, qayta ishga tushiring.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
