"""
Контекстное меню приложения с настройками времени, тем, звука и горячих клавиш.
"""

import tkinter as tk
from typing import Callable, Dict, Any
from .themes import THEMES
from ..utils.sound import SOUND_PRESETS


class TimerContextMenu:
    def __init__(
        self,
        parent: tk.Tk,
        on_toggle: Callable[[], None],
        on_reset: Callable[[], None],
        on_set_duration: Callable[[int], None],
        on_custom_time: Callable[[], None],
        on_set_theme: Callable[[str], None],
        on_choose_fg: Callable[[], None],
        on_choose_bg: Callable[[], None],
        on_choose_finish: Callable[[], None],
        on_set_alpha: Callable[[float], None],
        on_toggle_transparent_bg: Callable[[], None],
        on_toggle_topmost: Callable[[], None],
        on_toggle_sound: Callable[[], None],
        on_set_sound_type: Callable[[str], None],
        on_choose_custom_sound: Callable[[], None],
        on_preview_sound: Callable[[], None],
        on_toggle_global_hotkeys: Callable[[], None],
        on_exit: Callable[[], None],
        initial_topmost: bool = True,
        initial_sound: bool = True,
        initial_sound_type: str = "Дзынь (Ding)",
        initial_transparent_bg: bool = False,
        initial_global_hotkeys: bool = True
    ):
        self.menu = tk.Menu(parent, tearoff=0)

        # 1. Основное управление
        self.menu.add_command(label="▶ Старт / Пауза  (Пробел)", command=on_toggle)
        self.menu.add_command(label="↺ Сбросить  (R)", command=on_reset)
        self.menu.add_separator()

        # 2. Быстрое время
        presets_menu = tk.Menu(self.menu, tearoff=0)
        presets = [
            ("1 минута", 60),
            ("3 минуты", 180),
            ("5 минут", 300),
            ("10 минут", 600),
            ("15 минут", 900),
            ("20 минут", 1200),
            ("25 минут (Помодоро)", 1500),
            ("30 минут", 1800),
            ("45 минут", 2700),
            ("60 минут (1 час)", 3600),
        ]
        for name, secs in presets:
            presets_menu.add_command(
                label=name,
                command=lambda s=secs: on_set_duration(s)
            )
        self.menu.add_cascade(label="⏱ Быстрое время", menu=presets_menu)
        self.menu.add_command(label="⌨ Задать своё время...", command=on_custom_time)
        self.menu.add_separator()

        # 3. Темы оформления
        themes_menu = tk.Menu(self.menu, tearoff=0)
        for theme_name in THEMES.keys():
            themes_menu.add_command(
                label=theme_name,
                command=lambda t=theme_name: on_set_theme(t)
            )
        self.menu.add_cascade(label="🎨 Темы оформления", menu=themes_menu)

        # 4. Пользовательские цвета
        colors_menu = tk.Menu(self.menu, tearoff=0)
        colors_menu.add_command(label="Цвет цифр...", command=on_choose_fg)
        colors_menu.add_command(label="Цвет фона...", command=on_choose_bg)
        colors_menu.add_command(label="Цвет окончания...", command=on_choose_finish)
        self.menu.add_cascade(label="🖌 Свой цвет", menu=colors_menu)

        # 5. Чекбокс прозрачного фона
        self.transparent_bg_var = tk.BooleanVar(value=initial_transparent_bg)
        self.menu.add_checkbutton(
            label="👻 Прозрачный фон (только цифры)",
            variable=self.transparent_bg_var,
            command=on_toggle_transparent_bg
        )

        # 6. Прозрачность окна
        alpha_menu = tk.Menu(self.menu, tearoff=0)
        for val in [1.0, 0.9, 0.8, 0.7, 0.6]:
            pct = int(val * 100)
            alpha_menu.add_command(
                label=f"{pct}%",
                command=lambda a=val: on_set_alpha(a)
            )
        self.menu.add_cascade(label="👁 Прозрачность окна", menu=alpha_menu)

        # 7. Настройка звука окончания
        sound_submenu = tk.Menu(self.menu, tearoff=0)
        self.sound_var = tk.BooleanVar(value=initial_sound)
        sound_submenu.add_checkbutton(
            label="🔔 Включить звук",
            variable=self.sound_var,
            command=on_toggle_sound
        )
        sound_submenu.add_separator()

        # Выбор типа звука
        self.sound_type_var = tk.StringVar(value=initial_sound_type)
        for s_name in SOUND_PRESETS.keys():
            sound_submenu.add_radiobutton(
                label=s_name,
                variable=self.sound_type_var,
                value=s_name,
                command=lambda s=s_name: on_set_sound_type(s)
            )
        sound_submenu.add_radiobutton(
            label="Пользовательский (.wav)...",
            variable=self.sound_type_var,
            value="Пользовательский",
            command=on_choose_custom_sound
        )
        sound_submenu.add_separator()
        sound_submenu.add_command(label="▶ Прослушать звук", command=on_preview_sound)
        self.menu.add_cascade(label="🔔 Звук окончания", menu=sound_submenu)

        # 8. Горячие клавиши
        hotkeys_submenu = tk.Menu(self.menu, tearoff=0)
        self.global_hotkeys_var = tk.BooleanVar(value=initial_global_hotkeys)
        hotkeys_submenu.add_checkbutton(
            label="Глобальные: Ctrl+Alt+Space / R",
            variable=self.global_hotkeys_var,
            command=on_toggle_global_hotkeys
        )
        hotkeys_submenu.add_separator()
        hotkeys_submenu.add_command(label="В окне: Пробел — Старт/Пауза", state="disabled")
        hotkeys_submenu.add_command(label="В окне: R — Сброс", state="disabled")
        hotkeys_submenu.add_command(label="В окне: T — Поверх всех окон", state="disabled")
        hotkeys_submenu.add_command(label="В окне: Esc — Закрыть", state="disabled")
        self.menu.add_cascade(label="⌨ Горячие клавиши", menu=hotkeys_submenu)

        # 9. Закрепление поверх окон
        self.topmost_var = tk.BooleanVar(value=initial_topmost)
        self.menu.add_checkbutton(
            label="📌 Поверх всех окон (T)",
            variable=self.topmost_var,
            command=on_toggle_topmost
        )

        self.menu.add_separator()
        self.menu.add_command(label="✕ Закрыть  (Esc)", command=on_exit)

    def show(self, x: int, y: int):
        self.menu.tk_popup(x, y)
