"""
Yagona logging sozlamasi — barcha servislar shu funksiyani chaqiradi.
Loglar ham konsolga, ham logs/<servis>.log fayliga yoziladi.
Xabarlar aniq va tushunarli bo'lishi uchun formatlangan.
"""

import logging
import sys
from pathlib import Path

from core.config import LOGS_DIR

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def get_logger(service_name: str) -> logging.Logger:
    """Berilgan servis nomi uchun logger qaytaradi (masalan: 'orchestrator', 'bot')."""
    logger = logging.getLogger(service_name)
    if logger.handlers:
        return logger  # allaqachon sozlangan

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(_FORMAT, datefmt=_DATEFMT)

    # Konsolga chiqarish
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Faylga yozish
    try:
        Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            Path(LOGS_DIR) / f"{service_name}.log", encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as exc:
        # Fayl yozib bo'lmasa ham konsol logi ishlashda davom etadi
        logger.warning("Log fayli ochilmadi (%s), faqat konsolga yoziladi.", exc)

    logger.propagate = False
    return logger
