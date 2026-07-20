"""
02_obsidian_rag_sync.py  (REFERENCE / namuna)

Obsidian vault'ni kuzatib, matnlarni chunk qilib, OpenAI embedding
(text-embedding-3-small) orqali Supabase 'obsidian_chunks' jadvaliga yozadi.
RAG qidiruv uchun query_knowledge_base(question, top_k) funksiyasi tayyor.

ESLATMA: bu sizning mavjud faylingizga mos "reference" versiya. Sizda o'ziniki
bo'lsa, uni ishlating — muhimi: query_knowledge_base(question, top_k) imzosi
va u chunk ro'yxatini (source, content, similarity) qaytarishi bir xil bo'lsin.
Prism agent shu faylni importlib orqali yuklab, query_knowledge_base'ni chaqiradi.

Ishlash uchun .env dan quyidagilar kerak:
  OPENAI_API_KEY, EMBEDDING_MODEL, SUPABASE_URL, SUPABASE_SERVICE_KEY,
  OBSIDIAN_VAULT_PATH
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Bu faylni to'g'ridan-to'g'ri ishga tushirsa ham, agent importlib bilan
# yuklasa ham .env yuklanadi (agent o'zi ham yuklaydi — takror zarar qilmaydi).
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHUNK_SIZE = 800  # taxminan belgi (character) hisobida chunk kattaligi
CHUNK_OVERLAP = 150  # chunk'lar orasidagi ustma-ustlik (kontekst uzilmasligi uchun)


# --------------------------------------------------------------------------
# Klientlar (dangasa yuklash — import paytida xato bermasligi uchun)
# --------------------------------------------------------------------------
_openai_client = None
_supabase_client = None


def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        _openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _openai_client


def _get_supabase():
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client

        _supabase_client = create_client(
            os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]
        )
    return _supabase_client


# --------------------------------------------------------------------------
# Embedding
# --------------------------------------------------------------------------
def embed_text(text: str) -> list[float]:
    """Bitta matnni embedding vektoriga aylantiradi."""
    resp = _get_openai().embeddings.create(model=EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding


# --------------------------------------------------------------------------
# Chunking
# --------------------------------------------------------------------------
def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Matnni ustma-ust (overlap) chunk'larga bo'ladi."""
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        start = end - overlap
        if start < 0:
            start = 0
        if end >= len(text):
            break
    return [c for c in chunks if c]


# --------------------------------------------------------------------------
# Vault sync — barcha .md fayllarni Supabase'ga yozadi
# --------------------------------------------------------------------------
def sync_vault(vault_path: str | None = None) -> int:
    """
    Obsidian vault'dagi barcha .md fayllarni o'qib, chunk qilib, embed qilib,
    obsidian_chunks jadvaliga upsert qiladi. Yozilgan chunk'lar sonini qaytaradi.
    """
    vault = Path(vault_path or os.environ["OBSIDIAN_VAULT_PATH"])
    supa = _get_supabase()
    total = 0
    for md_file in vault.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError:
            continue
        source = str(md_file.relative_to(vault))
        chunks = chunk_text(content)
        rows = []
        for idx, chunk in enumerate(chunks):
            rows.append(
                {
                    "source": source,
                    "chunk_index": idx,
                    "content": chunk,
                    "embedding": embed_text(chunk),
                }
            )
        if rows:
            supa.table("obsidian_chunks").upsert(
                rows, on_conflict="source,chunk_index"
            ).execute()
            total += len(rows)
    return total


# --------------------------------------------------------------------------
# RAG qidiruv — agent shu funksiyani chaqiradi
# --------------------------------------------------------------------------
def query_knowledge_base(question: str, top_k: int = 5) -> list[dict]:
    """
    Savolni embed qilib, match_obsidian_chunks RPC orqali eng mos chunk'larni oladi.

    Qaytaradi: list[dict] — har biri {source, content, similarity} kalitlariga ega.
    (Prism agent shu ro'yxatni matnga aylantirib Claude'ga beradi.)
    """
    if not question or not question.strip():
        return []
    embedding = embed_text(question)
    supa = _get_supabase()
    resp = supa.rpc(
        "match_obsidian_chunks",
        {"query_embedding": embedding, "match_count": top_k},
    ).execute()
    return resp.data or []


if __name__ == "__main__":
    # Qo'lda ishga tushirish: python 02_obsidian_rag_sync.py sync
    #                          python 02_obsidian_rag_sync.py query "savol"
    if len(sys.argv) >= 2 and sys.argv[1] == "sync":
        n = sync_vault()
        print(f"Sync tugadi: {n} ta chunk yozildi.")
    elif len(sys.argv) >= 3 and sys.argv[1] == "query":
        for row in query_knowledge_base(sys.argv[2]):
            print(f"[{row.get('similarity', 0):.3f}] {row.get('source')}: "
                  f"{row.get('content', '')[:120]}...")
    else:
        print("Foydalanish: python 02_obsidian_rag_sync.py [sync | query \"savol\"]")
