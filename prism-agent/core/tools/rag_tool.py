"""
RAG tool — bilim bazasidan (Obsidian chunks) qidiruv.

02_obsidian_rag_sync.py'dagi query_knowledge_base() funksiyasi importlib orqali
yuklanadi (fayl nomi raqamdan boshlangani uchun oddiy import ishlamaydi).
Claude 'search_knowledge_base' tool'ini chaqirganda ishga tushadi.
"""

import asyncio
import importlib.util
from pathlib import Path

from core import config
from core.logging_setup import get_logger
from core.tools.base import RunContext

log = get_logger("rag_tool")

# query_knowledge_base funksiyasi bir marta yuklanib, keshlanadi
_query_fn = None
_load_error: str | None = None


def _load_query_fn():
    """02_obsidian_rag_sync.py'dan query_knowledge_base'ni yuklaydi (keshlanadi)."""
    global _query_fn, _load_error
    if _query_fn is not None or _load_error is not None:
        return _query_fn

    module_path = Path(config.OBSIDIAN_RAG_MODULE_PATH)
    if not module_path.exists():
        _load_error = (
            f"RAG moduli topilmadi: {module_path}. "
            "OBSIDIAN_RAG_MODULE_PATH ni .env da to'g'ri ko'rsating."
        )
        log.error(_load_error)
        return None

    try:
        spec = importlib.util.spec_from_file_location("obsidian_rag_sync", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        _query_fn = module.query_knowledge_base
        log.info("query_knowledge_base yuklandi: %s", module_path)
    except Exception as exc:  # import xatosi bo'lsa tool ishlamaydi, lekin bot yiqilmaydi
        _load_error = f"RAG modulini yuklashda xato: {exc}"
        log.exception("RAG modulini yuklashda xato")
    return _query_fn


def _format_results(results) -> str:
    """
    query_knowledge_base natijasini Claude uchun matnga aylantiradi.
    Turli qaytish formatlariga chidamli: str, list[str], yoki list[dict].
    """
    if not results:
        return "Bilim bazasidan hech narsa topilmadi."
    if isinstance(results, str):
        return results

    parts = []
    for i, item in enumerate(results, 1):
        if isinstance(item, dict):
            source = item.get("source") or item.get("title") or "manba"
            content = item.get("content") or item.get("text") or ""
            sim = item.get("similarity")
            header = f"[{i}] {source}"
            if isinstance(sim, (int, float)):
                header += f" (moslik: {sim:.2f})"
            parts.append(f"{header}\n{content}")
        else:
            parts.append(f"[{i}] {item}")
    return "\n\n".join(parts)


SPEC = {
    "name": "search_knowledge_base",
    "description": (
        "Prism agentligining ichki bilim bazasidan (Obsidian yozuvlari) "
        "ma'lumot qidiradi. Mijozlar, funnel'lar, CustDev, case'lar, "
        "ichki jarayonlar haqidagi savollarda ishlat."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Bilim bazasidan qidiriladigan savol yoki kalit so'zlar.",
            },
            "top_k": {
                "type": "integer",
                "description": "Qaytariladigan eng mos chunk'lar soni (default 5).",
                "default": 5,
            },
        },
        "required": ["question"],
    },
}


async def handler(tool_input: dict, ctx: RunContext) -> str:
    """Bilim bazasidan qidiradi va topilgan kontekstni qaytaradi."""
    question = tool_input.get("question", "")
    top_k = int(tool_input.get("top_k", 5) or 5)

    query_fn = _load_query_fn()
    if query_fn is None:
        return f"[XATO] Bilim bazasi hozircha mavjud emas: {_load_error}"

    try:
        # query_knowledge_base sinxron (OpenAI + Supabase) — event loop'ni bloklamaslik
        # uchun alohida threadda ishlatamiz.
        results = await asyncio.to_thread(query_fn, question, top_k)
    except Exception as exc:
        log.exception("Bilim bazasi qidiruvida xato")
        return f"[XATO] Bilim bazasi qidiruvida xato: {exc}"

    log.info("RAG qidiruv: %r -> %s natija", question, _count(results))
    return _format_results(results)


def _count(results) -> int:
    if results is None:
        return 0
    if isinstance(results, str):
        return 1
    try:
        return len(results)
    except TypeError:
        return 0
