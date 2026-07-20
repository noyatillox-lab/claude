"""
RAG tool — bilim bazasidan (Obsidian chunks) qidiruv.

BOSQICH 1: stub (bo'sh). Faqat routing tekshiriladi.
BOSQICH 3: 02_obsidian_rag_sync.py'dagi query_knowledge_base() bu yerga ulanadi.
"""

from core.tools.base import RunContext

# Claude'ga beriladigan tool ta'rifi (schema)
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
    """BOSQICH 1 stub — hali real qidiruv ulanmagan."""
    question = tool_input.get("question", "")
    return (
        f"[STUB search_knowledge_base] So'rov qabul qilindi: {question!r}. "
        "Bilim bazasi Bosqich 3'da ulanadi."
    )
