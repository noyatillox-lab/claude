"""
Rasm generatsiya tool — Replicate (Flux/Ideogram) orqali.

BOSQICH 1: stub. BOSQICH 4: Replicate API ulanadi va rasm URL qaytadi.
"""

from core.tools.base import RunContext

SPEC = {
    "name": "generate_image",
    "description": (
        "Matnli tavsif (prompt) asosida rasm generatsiya qiladi. "
        "Foydalanuvchi 'rasm chizib ber', 'banner yasab ber', 'visual kerak' "
        "degan buyruq berganda ishlat."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Rasmning ingliz tilidagi batafsil tavsifi (prompt).",
            },
            "aspect_ratio": {
                "type": "string",
                "description": "Tomonlar nisbati, masalan '1:1', '16:9', '9:16'.",
                "default": "1:1",
            },
        },
        "required": ["prompt"],
    },
}


async def handler(tool_input: dict, ctx: RunContext) -> str:
    """BOSQICH 1 stub — Replicate hali ulanmagan."""
    prompt = tool_input.get("prompt", "")
    return (
        f"[STUB generate_image] Prompt qabul qilindi: {prompt!r}. "
        "Rasm generatsiya Bosqich 4'da ulanadi."
    )
