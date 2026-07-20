"""
Rasm generatsiya tool — Replicate (Flux/Ideogram) orqali.

Claude 'generate_image' tool'ini chaqirganda ishga tushadi. Natija rasm URL(lar)i
RunContext'ga qo'shiladi — orkestrator/bot ularni foydalanuvchiga yuboradi.
"""

from core import config
from core.logging_setup import get_logger
from core.tools.base import RunContext

log = get_logger("image_tool")

# Replicate klienti bir marta yaratilib keshlanadi
_client = None


def _get_client():
    global _client
    if _client is None:
        import replicate

        if not config.REPLICATE_API_TOKEN:
            raise RuntimeError("REPLICATE_API_TOKEN topilmadi. .env faylini to'ldiring.")
        _client = replicate.Client(api_token=config.REPLICATE_API_TOKEN)
    return _client


def _extract_urls(output) -> list[str]:
    """
    Replicate natijasidan URL'larni ajratadi. Model turiga qarab natija:
    string, list, yoki .url atributi bo'lgan FileOutput obyekt bo'lishi mumkin.
    """
    items = output if isinstance(output, list) else [output]
    urls: list[str] = []
    for it in items:
        if it is None:
            continue
        if isinstance(it, str):
            urls.append(it)
        elif hasattr(it, "url"):
            urls.append(it.url)
        else:
            urls.append(str(it))
    return urls


async def _run_replicate(prompt: str, aspect_ratio: str) -> list[str]:
    """Replicate modelini ishga tushirib, rasm URL'larini qaytaradi."""
    client = _get_client()
    output = await client.async_run(
        config.REPLICATE_IMAGE_MODEL,
        input={
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": "png",
        },
    )
    return _extract_urls(output)


SPEC = {
    "name": "generate_image",
    "description": (
        "Matnli tavsif (prompt) asosida rasm generatsiya qiladi. "
        "Foydalanuvchi 'rasm chizib ber', 'banner yasab ber', 'visual kerak' "
        "degan buyruq berganda ishlat. Prompt ingliz tilida va batafsil bo'lishi kerak."
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
                "description": "Tomonlar nisbati: '1:1', '16:9', '9:16', '4:5'.",
                "default": "1:1",
            },
        },
        "required": ["prompt"],
    },
}


async def handler(tool_input: dict, ctx: RunContext) -> str:
    """Rasm generatsiya qiladi va URL'ini kontekstga qo'shadi."""
    prompt = tool_input.get("prompt", "").strip()
    if not prompt:
        return "[XATO] Rasm uchun prompt bo'sh bo'lmasligi kerak."
    aspect_ratio = tool_input.get("aspect_ratio", "1:1") or "1:1"

    try:
        urls = await _run_replicate(prompt, aspect_ratio)
    except Exception as exc:
        log.exception("Rasm generatsiyada xato")
        return f"[XATO] Rasm generatsiya qilinmadi: {exc}"

    if not urls:
        return "[XATO] Model rasm qaytarmadi."

    for url in urls:
        ctx.add_image(url)  # bot shu URL'lardan rasmni yuboradi

    log.info("Rasm generatsiya qilindi: %d ta (%s)", len(urls), aspect_ratio)
    # Claude'ga URL'ni qaytaramiz, u foydalanuvchiga qisqa izoh yozadi
    return "Rasm tayyor bo'ldi va foydalanuvchiga yuborilmoqda. URL: " + ", ".join(urls)
