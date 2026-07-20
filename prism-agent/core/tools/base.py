"""
Tool'lar uchun umumiy asos: RunContext.

RunContext bitta suhbat (agent yugurishi) davomida to'planadigan
qo'shimcha natijalarni (masalan generatsiya qilingan rasm URL'lari)
saqlaydi. Tool handler'lari matn qaytaradi (Claude'ga), lekin yon
natijalarni (rasm, fayl) shu kontekstga qo'shadi — orkestrator ularni
oxirida foydalanuvchiga (botga) yetkazadi.
"""

from dataclasses import dataclass, field


@dataclass
class RunContext:
    """Bitta agent yugurishining konteksti."""

    # Foydalanuvchi haqida ma'lumot (Telegram user id va h.k.) — kelajakda kengayadi
    user_id: int | None = None
    # Tool'lar davomida to'plangan rasm URL'lari
    image_urls: list[str] = field(default_factory=list)

    def add_image(self, url: str) -> None:
        """Generatsiya qilingan rasm URL'ini natijaga qo'shadi."""
        if url:
            self.image_urls.append(url)
