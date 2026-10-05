"""
Утилиты времени и форматирования.
"""

import re
from typing import Optional


def parse_time_input(text: str) -> Optional[int]:
    """
    Универсальный парсер строки времени в секунды.
    Поддерживает:
      - Числа: '15' -> 900 сек (15 мин), '0.5' -> 30 сек
      - Формат с двоеточием: '10:00', '01:15:30'
      - Текстовые суффиксы: '15m', '45s', '1h 30m', '1ч 20м 10с'
    """
    if not text:
        return None

    text = text.strip().lower()
    if not text:
        return None

    # Формат ЧЧ:ММ:СС или ММ:СС
    if ":" in text:
        parts = text.split(":")
        try:
            if len(parts) == 2:
                m, s = int(parts[0]), int(parts[1])
                return m * 60 + s
            elif len(parts) == 3:
                h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                return h * 3600 + m * 60 + s
        except ValueError:
            return None

    # Формат вида '1h 30m 15s' или '1ч 30м 15с'
    pattern = (
        r'(?:(\d+)\s*(?:h|ч|час|часа|часов))?\s*'
        r'(?:(\d+)\s*(?:m|м|мин|минут|минуты))?\s*'
        r'(?:(\d+)\s*(?:s|с|сек|секунд))?'
    )
    match = re.fullmatch(pattern, text)
    if match and any(match.groups()):
        h = int(match.group(1)) if match.group(1) else 0
        m = int(match.group(2)) if match.group(2) else 0
        s = int(match.group(3)) if match.group(3) else 0
        total = h * 3600 + m * 60 + s
        if total > 0:
            return total

    # Просто число -> считаем минутами
    try:
        val = float(text)
        return int(round(val * 60))
    except ValueError:
        pass

    return None


def format_time(seconds: float, show_hours: bool = True) -> str:
    """
    Форматирует секунды в строку 'ЧЧ:ММ:СС' или 'ММ:СС'.
    """
    total_secs = max(0, int(round(seconds)))
    hours, remainder = divmod(total_secs, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours > 0 or show_hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
