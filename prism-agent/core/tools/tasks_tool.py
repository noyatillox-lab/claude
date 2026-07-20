"""
Vazifalar tool — Supabase 'tasks' jadvaliga CRUD.

BOSQICH 1: stub. BOSQICH 5: real Supabase jadvaliga yozadi/o'qiydi.
(Jadval schema'si foydalanuvchidan olinadi.)
"""

from core.tools.base import RunContext

SPEC = {
    "name": "create_task",
    "description": (
        "Jamoa a'zosiga yangi vazifa (task) yaratadi. "
        "Foydalanuvchi 'X ga shu vazifani ber' desa ishlat."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Vazifa matni / sarlavhasi.",
            },
            "assignee": {
                "type": "string",
                "description": "Vazifa biriktirilgan jamoa a'zosining ismi.",
            },
            "due_date": {
                "type": "string",
                "description": "Muddat (ixtiyoriy), ISO format: YYYY-MM-DD.",
            },
        },
        "required": ["title", "assignee"],
    },
}


async def handler(tool_input: dict, ctx: RunContext) -> str:
    """BOSQICH 1 stub — Supabase jadvaliga yozish Bosqich 5'da ulanadi."""
    title = tool_input.get("title", "")
    assignee = tool_input.get("assignee", "")
    return (
        f"[STUB create_task] Vazifa qabul qilindi: {title!r} -> {assignee!r}. "
        "Supabase 'tasks' jadvaliga yozish Bosqich 5'da ulanadi."
    )
