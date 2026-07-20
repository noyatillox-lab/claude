"""
Orkestrator — Prism agentining miyasi.

Vazifasi:
  1. Foydalanuvchi xabarini Claude API'ga yuboradi (tool'lar bilan).
  2. Agar Claude biror tool chaqirsa (tool_use), tegishli handler'ni ishga
     tushiradi va natijani Claude'ga qaytaradi (tool_result).
  3. Claude tool chaqirmay, matnli javob berguncha tsikl davom etadi.
  4. Yakuniy matn va yon natijalar (rasm URL'lari) qaytariladi.

Bosqich 1'da tool'lar stub, lekin routing to'liq ishlaydi.
"""

from dataclasses import dataclass, field

from anthropic import AsyncAnthropic

from core import config
from core.logging_setup import get_logger
from core.tools import TOOL_SPECS, RunContext, dispatch

log = get_logger("orchestrator")

# Tool-use tsikli cheksiz bo'lib qolmasligi uchun maksimal aylanish
_MAX_TOOL_ROUNDS = 8

# Claude'ning xatti-harakatini belgilovchi tizim ko'rsatmasi.
# Javoblar o'zbekcha (lotin), lekin marketing/tech atamalar ingliz tilida.
SYSTEM_PROMPT = """\
Sen Prism Marketing agentligining ichki AI yordamchisisan. Prism — Toshkentdagi \
performance marketing, lead-gen va funnel qurish agentligi.

QOIDALAR:
- Foydalanuvchiga o'zbek tilida (lotin alifbosida) javob ber.
- Marketing va texnik atamalarni ingliz tilida qoldir: funnel, CustDev, ad copy, \
lead, CTR, CPL, landing, creative, retention va h.k.
- Qisqa, aniq va ishga yaroqli javob ber. Ortiqcha muqaddima yozma.
- Kerak bo'lganda tool'lardan foydalan: bilim bazasi qidiruvi, rasm generatsiya, \
vazifa yaratish. Javobni to'qib chiqarma — ma'lumot kerak bo'lsa bilim bazasidan qidir.
"""


@dataclass
class AgentResult:
    """Orkestrator yakuniy natijasi."""

    text: str
    image_urls: list[str] = field(default_factory=list)
    # Yangilangan suhbat tarixi (keyingi xabarda uzatish uchun)
    history: list[dict] = field(default_factory=list)


class Orchestrator:
    """Claude API + tool-use routing markazi."""

    def __init__(self) -> None:
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY topilmadi. .env faylini to'ldiring."
            )
        self._client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

    async def run(
        self,
        user_text: str,
        history: list[dict] | None = None,
        user_id: int | None = None,
    ) -> AgentResult:
        """
        Foydalanuvchi xabarini qayta ishlaydi.

        history — oldingi suhbat (Anthropic 'messages' formati). None bo'lsa yangi
        suhbat boshlanadi. Qaytadigan AgentResult.history keyingi chaqiruvda uzatiladi.
        """
        ctx = RunContext(user_id=user_id)
        messages: list[dict] = list(history or [])
        messages.append({"role": "user", "content": user_text})

        for round_num in range(1, _MAX_TOOL_ROUNDS + 1):
            log.info("Claude'ga so'rov (round %d), xabarlar: %d", round_num, len(messages))
            response = await self._client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=config.CLAUDE_MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=TOOL_SPECS,
                messages=messages,
            )

            # Claude javobini tarixga qo'shamiz (assistant turn)
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                # Tool chaqirilmadi — yakuniy matnli javob
                final_text = _extract_text(response.content)
                log.info("Yakuniy javob tayyor (round %d).", round_num)
                return AgentResult(
                    text=final_text,
                    image_urls=ctx.image_urls,
                    history=messages,
                )

            # Claude bir yoki bir nechta tool chaqirdi — hammasini bajaramiz
            tool_results = []
            for block in response.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                log.info("Tool chaqirildi: %s | input=%s", block.name, block.input)
                try:
                    result_text = await dispatch(block.name, dict(block.input), ctx)
                except Exception as exc:  # tool ichidagi xatoni Claude'ga qaytaramiz
                    log.exception("Tool xatosi: %s", block.name)
                    result_text = f"[XATO] Tool '{block.name}' ishlamadi: {exc}"
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    }
                )

            # Tool natijalarini foydalanuvchi turn sifatida qaytaramiz
            messages.append({"role": "user", "content": tool_results})

        # Tsikl cheklovi tugadi — himoya javobi
        log.warning("Tool tsikli maksimal aylanishga yetdi (%d).", _MAX_TOOL_ROUNDS)
        return AgentResult(
            text="Kechirasiz, so'rov juda ko'p qadam talab qildi. Iltimos, "
            "savolni soddalashtirib qayta yuboring.",
            image_urls=ctx.image_urls,
            history=messages,
        )


def _extract_text(content_blocks) -> str:
    """Claude javob bloklaridan matnni yig'ib beradi."""
    parts = []
    for block in content_blocks:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts).strip() or "(bo'sh javob)"
