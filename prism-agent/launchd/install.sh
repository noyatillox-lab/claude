#!/usr/bin/env bash
# ============================================================
# Prism launchd servislarini o'rnatish skripti (Mac mini).
# Plist shablonlaridagi <PRISM_DIR>, <PYTHON>, <RAG_SCRIPT> ni to'ldiradi
# va ~/Library/LaunchAgents/ ga o'rnatib, ishga tushiradi.
#
# Foydalanish:
#   ./install.sh                 # avtomatik aniqlaydi
#   PRISM_DIR=... PYTHON=... ./install.sh
# ============================================================
set -euo pipefail

# Loyiha papkasi (bu skript joylashgan joyning bir pog'ona tepasi)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRISM_DIR="${PRISM_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
# venv python bo'lsa o'shani, aks holda tizim python3
PYTHON="${PYTHON:-$PRISM_DIR/.venv/bin/python3}"
if [ ! -x "$PYTHON" ]; then
    PYTHON="$(command -v python3)"
fi
# 02_obsidian_rag_sync.py yo'li (repo ildizida — bir pog'ona tepada)
RAG_SCRIPT="${RAG_SCRIPT:-$(cd "$PRISM_DIR/.." && pwd)/02_obsidian_rag_sync.py}"

LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS" "$PRISM_DIR/logs"

echo "PRISM_DIR = $PRISM_DIR"
echo "PYTHON    = $PYTHON"
echo "RAG_SCRIPT= $RAG_SCRIPT"

for plist in com.prism.bot com.prism.watcher com.prism.ragsync; do
    src="$SCRIPT_DIR/$plist.plist"
    dst="$LAUNCH_AGENTS/$plist.plist"
    echo "-> $plist o'rnatilmoqda..."
    sed -e "s#<PRISM_DIR>#$PRISM_DIR#g" \
        -e "s#<PYTHON>#$PYTHON#g" \
        -e "s#<RAG_SCRIPT>#$RAG_SCRIPT#g" \
        "$src" > "$dst"
    # Avval to'xtatib, keyin qayta yuklaymiz (idempotent)
    launchctl unload "$dst" 2>/dev/null || true
    launchctl load "$dst"
done

echo "Tayyor. Holatni tekshirish: launchctl list | grep com.prism"
echo "ESLATMA: com.prism.watcher birinchi marta telefon/kod so'raydi —"
echo "avval bir marta qo'lda 'python -m monitor.group_watcher' ishlatib sessiya yarating."
