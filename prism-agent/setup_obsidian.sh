#!/usr/bin/env bash
# ============================================================
# Obsidian integratsiyasini bir komandada sozlaydi (Mac mini'da ishga tushiring).
#   1) venv yaratadi + kutubxonalarni o'rnatadi
#   2) .env borligini tekshiradi (yo'q bo'lsa namunadan yaratadi)
#   3) ulanishni tekshiradi (OpenAI + Supabase + vault)
#   4) Obsidian yozuvlarini Supabase'ga sync qiladi
#   5) test qidiruv qiladi
#
# Foydalanish:
#   cd prism-agent
#   chmod +x setup_obsidian.sh
#   ./setup_obsidian.sh
# ============================================================
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"   # prism-agent papkasiga o'tamiz
echo "== Prism Obsidian sozlash =="

# --- 1) venv + kutubxonalar ---
if [ ! -d ".venv" ]; then
    echo "[1/5] Virtual muhit yaratilmoqda..."
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
echo "[1/5] Kutubxonalar o'rnatilmoqda..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# --- 2) .env ---
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo ">>> .env yaratildi. Iltimos, uni oching va to'ldiring:"
    echo ">>>   OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, OBSIDIAN_VAULT_PATH"
    echo ">>> Keyin shu skriptni QAYTA ishga tushiring."
    echo ">>>   nano .env    (yoki: open -e .env)"
    exit 0
fi

# --- 3) ulanish tekshiruvi ---
echo "[3/5] Ulanish tekshirilmoqda..."
if ! python scripts/check_env.py; then
    echo ">>> Yuqoridagi xatolarni tuzatib, skriptni qayta ishga tushiring."
    exit 1
fi

# --- 4) sync ---
RAG_SCRIPT="$(python -c 'from core import config; print(config.OBSIDIAN_RAG_MODULE_PATH)')"
echo "[4/5] Obsidian sync (bu biroz vaqt olishi mumkin)..."
python "$RAG_SCRIPT" sync

# --- 5) test qidiruv ---
echo "[5/5] Test qidiruv..."
python "$RAG_SCRIPT" query "test" || true

echo ""
echo "✅ Tayyor! Obsidian bilim bazasi Supabase'ga yuklandi."
echo "Endi botga savol bersangiz, u shu yozuvlardan javob topadi."
