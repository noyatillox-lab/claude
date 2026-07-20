"""
Tool registri — barcha Claude tool'lari shu yerda ro'yxatga olinadi.

Har bir tool moduli ikki usuldan birida tool(lar)ini e'lon qiladi:
  1) Bitta tool:  SPEC (dict) + handler(tool_input, ctx) -> str
  2) Bir nechta tool:  get_tools() -> list[tuple[spec_dict, handler]]

Yangi modul qo'shish: import qiling va _MODULES ro'yxatiga qo'shing.
"""

from core.tools import image_tool, rag_tool, tasks_tool
from core.tools.base import RunContext

# Ro'yxatga olingan tool modullari
_MODULES = [rag_tool, image_tool, tasks_tool]


def _module_tools(module) -> list[tuple[dict, object]]:
    """Moduldan (spec, handler) juftliklari ro'yxatini oladi (ikki uslubga chidamli)."""
    if hasattr(module, "get_tools"):
        return list(module.get_tools())
    return [(module.SPEC, module.handler)]


# Barcha modullardan tool'larni yig'amiz
_ALL: list[tuple[dict, object]] = []
for _m in _MODULES:
    _ALL.extend(_module_tools(_m))

# Claude'ga yuboriladigan tool schema'lari
TOOL_SPECS = [spec for spec, _ in _ALL]

# Tool nomi -> handler funksiya
TOOL_HANDLERS = {spec["name"]: handler for spec, handler in _ALL}


async def dispatch(name: str, tool_input: dict, ctx: RunContext) -> str:
    """Tool nomini topib, tegishli handler'ni chaqiradi."""
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return f"[XATO] Noma'lum tool: {name}"
    return await handler(tool_input, ctx)


__all__ = ["TOOL_SPECS", "TOOL_HANDLERS", "RunContext", "dispatch"]
