"""
Модуль конфигурации и сохранения настроек.
"""

import sys
import os
import json
from typing import Dict, Any


def get_config_dir() -> str:
    """
    Возвращает директорию для хранения конфигурации.
    Если собрано в exe - рядом с exe, иначе в корне проекта.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # 2 уровня выше src/timer_app/config.py -> корень проекта
    current_file = os.path.abspath(__file__)
    pkg_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    return pkg_dir


CONFIG_FILE_NAME = "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "initial_time": 900,
    "theme": "Тёмная (Dark)",
    "bg_color": "#181825",
    "fg_color": "#cdd6f4",
    "finish_color": "#f38ba8",
    "transparent_bg": False,
    "topmost": True,
    "alpha": 1.0,
    "sound_enabled": True,
    "sound_type": "Дзынь (Ding)",
    "custom_sound_path": "",
    "global_hotkeys_enabled": True,
    "show_hours": True,
    "total_rounds": 1,
    "rest_duration": 0,
    "window_x": None,
    "window_y": None,
    "window_width": 330,
    "window_height": 96
}


class ConfigManager:
    def __init__(self, file_path: str = None):
        if file_path is None:
            self.file_path = os.path.join(get_config_dir(), CONFIG_FILE_NAME)
        else:
            self.file_path = file_path
        self.data = self.load()

    def load(self) -> Dict[str, Any]:
        config = DEFAULT_CONFIG.copy()
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    config.update(loaded)
            except Exception as e:
                print(f"[ConfigManager] Ошибка чтения {self.file_path}: {e}")
        return config

    def save(self) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ConfigManager] Ошибка сохранения {self.file_path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
