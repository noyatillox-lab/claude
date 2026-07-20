"""
Ism matcher — matn ichida ismni (variantlari bilan) imlo xatosiga chidamli topadi.

rapidfuzz yordamida "sliding window" usuli: har bir variant necha so'zdan iborat
bo'lsa, matndagi shuncha so'zli oynalar bilan solishtiriladi. Bu "Maks Tur" kabi
ko'p so'zli ismlarni ham, "Maksim" kabi bitta so'zni ham topadi.
"""

import re
from dataclasses import dataclass

from rapidfuzz import fuzz

# Standart o'xshashlik chegarasi (0..100). Undan yuqori bo'lsa — moslik topildi deb hisoblanadi.
DEFAULT_THRESHOLD = 88

# O'zbekcha keng tarqalgan qo'shimchalar (kelishik/egalik). Ism ustiga qo'shilganda
# ("Maksga", "Maksni", "Maksdan") ularni olib tashlab, o'zak bilan solishtiramiz.
# Uzunroqlari birinchi tekshiriladi (masalan 'larning' 'lar'dan oldin).
_SUFFIXES = sorted(
    [
        "larning", "lardan", "larga", "larda", "larni", "lar",
        "ning", "niki", "niki", "dan", "ga", "ka", "qa", "da",
        "ni", "cha", "dek", "day", "imiz", "ingiz", "im", "ing", "si", "miz",
    ],
    key=len,
    reverse=True,
)


def _stem(word: str) -> str:
    """So'zdan bitta o'zbekcha qo'shimchani olib tashlaydi (o'zak >= 3 harf qolsa)."""
    for suf in _SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            return word[: -len(suf)]
    return word


@dataclass
class NameMatch:
    """Topilgan moslik haqida ma'lumot."""

    variant: str  # qaysi variant mos keldi
    score: float  # o'xshashlik bahosi (0..100)
    matched_text: str  # matndagi haqiqiy topilgan qism


def _normalize(text: str) -> str:
    """Kichik harf, tinish belgilarini bo'shliqqa aylantirish, ortiqcha bo'shliqni siqish."""
    text = text.lower()
    # Harf va raqamdan boshqa hamma narsani bo'shliqqa aylantiramiz (Kirill/Lotin qoladi)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_name(
    text: str,
    variants: list[str],
    threshold: int = DEFAULT_THRESHOLD,
) -> NameMatch | None:
    """
    Matnda berilgan ism variantlaridan birini qidiradi.
    Topilsa eng yuqori baholi NameMatch, aks holda None qaytaradi.
    """
    if not text or not variants:
        return None

    norm_text = _normalize(text)
    if not norm_text:
        return None
    words = norm_text.split()
    # So'zlarning qo'shimchasiz o'zaklari (Maksga -> maks) — parallel tekshiramiz
    stems = [_stem(w) for w in words]

    best: NameMatch | None = None
    for variant in variants:
        norm_variant = _normalize(variant)
        if not norm_variant:
            continue
        n = len(norm_variant.split())
        if n <= 0 or n > len(words):
            continue

        # Matndagi har bir n-so'zli oynani (asl va o'zak ko'rinishida) variant bilan solishtiramiz
        for i in range(len(words) - n + 1):
            for source in (words, stems):
                window = " ".join(source[i : i + n])
                score = fuzz.ratio(window, norm_variant)
                if score >= threshold and (best is None or score > best.score):
                    best = NameMatch(variant=variant, score=score, matched_text=window)

    return best
