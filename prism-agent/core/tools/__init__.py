"""
Tool registri — barcha Claude tool'lari shu yerda ro'yxatga olinadi.

Yangi tool qo'shish: modulni import qiling va _MODULES ro'yxatiga qo'shing.
Har bir tool moduli ikkitasini eksport qilishi shart:
  - SPEC: Claude'ga beriladigan tool schema (dict)
  - handler(tool_input: dict, ctx: RunContext) -> str  (async)
"""

from core.tools import image_tool, rag_tool, tasks_tool
from core.tools.base import RunContext

# Ro'yxatga olingan tool modullari
_MODULES = [rag_tool, image_tool, tasks_tool]

# Claude'ga yuboriladigan tool schema'lari ro'yxati
TOOL_SPECS = [m.SPEC for m in _MODULES]

# Tool nomi -> handler funksiya
TOOL_HANDLERS = {m.SPEC["name"]: m.handler for m in _MODULES}


async def dispatch(name: str, tool_input: dict, ctx: RunContext) -> str:
    """Tool nomini topib, tegishli handler'ni chaqiradi."""
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return f"[XATO] Noma'lum tool: {name}"
    return await handler(tool_input, ctx)


__all__ = ["TOOL_SPECS", "TOOL_HANDLERS", "RunContext", "dispatch"]
