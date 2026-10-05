"""
Цветовые темы и оформление.
"""

from typing import Dict

THEMES: Dict[str, Dict[str, str]] = {
    "Тёмная (Dark)": {
        "bg": "#181825",
        "fg": "#cdd6f4",
        "finish": "#f38ba8"
    },
    "Светлая (Light)": {
        "bg": "#f5f5f7",
        "fg": "#1d1d1f",
        "finish": "#ff3b30"
    },
    "Матрица / Неон": {
        "bg": "#0a0e14",
        "fg": "#00ff66",
        "finish": "#ff0055"
    },
    "Киберпанк": {
        "bg": "#0f051d",
        "fg": "#00f0ff",
        "finish": "#ff007f"
    },
    "Янтарь (Amber)": {
        "bg": "#1c1917",
        "fg": "#f59e0b",
        "finish": "#ef4444"
    },
    "Изумрудная (Emerald)": {
        "bg": "#062820",
        "fg": "#34d399",
        "finish": "#f87171"
    },
    "Глубокий синий (Midnight)": {
        "bg": "#0a192f",
        "fg": "#38bdf8",
        "finish": "#fb7185"
    }
}
