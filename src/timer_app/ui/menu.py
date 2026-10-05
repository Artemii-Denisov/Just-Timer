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
        on_toggle_round_sound: Callable[[], None],
        on_set_round_sound_type: Callable[[str], None],
        on_choose_round_custom_sound: Callable[[], None],
        on_preview_round_sound: Callable[[], None],
        on_toggle_global_hotkeys: Callable[[], None],
        on_set_rounds: Callable[[int, float, float], None],
        on_custom_rounds: Callable[[], None],
        on_toggle_infinite_loop: Callable[[], None],
        on_exit: Callable[[], None],
        initial_topmost: bool = True,
        initial_sound: bool = True,
        initial_sound_type: str = "Дзынь (Ding)",
        initial_round_sound: bool = True,
        initial_round_sound_type: str = "Короткий сигнал (Beep)",
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

        # 3. Круги и циклы (раунды)
        rounds_menu = tk.Menu(self.menu, tearoff=0)
        rounds_menu.add_command(
            label="⏹ Обычный режим (1 круг)",
            command=lambda: on_set_rounds(1, 900, 0)
        )
        rounds_menu.add_separator()
        round_presets = [
            ("🔁 5 кругов по 30 сек", 5, 30, 0),
            ("🔁 5 кругов по 30 сек (+10с отдых)", 5, 30, 10),
            ("🔁 3 круга по 1 мин", 3, 60, 0),
            ("🔁 4 круга по 1 мин (+15с отдых)", 4, 60, 15),
            ("🔁 5 кругов по 2 мин", 5, 120, 0),
            ("🔁 8 кругов Табата (20с / 10с отдых)", 8, 20, 10),
            ("🔁 4 круга Помодоро (25м / 5м отдых)", 4, 1500, 300),
        ]
        for title, count, work, rest in round_presets:
            rounds_menu.add_command(
                label=title,
                command=lambda c=count, w=work, r=rest: on_set_rounds(c, w, r)
            )
        rounds_menu.add_separator()
        rounds_menu.add_command(label="⚙ Настроить свои круги...", command=on_custom_rounds)
        rounds_menu.add_command(label="♾ Бесконечный цикл (автоповтор)", command=on_toggle_infinite_loop)
        self.menu.add_cascade(label="🔁 Круги и циклы", menu=rounds_menu)
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
        self.menu.add_cascade(label="🔔 Звук окончания таймера", menu=sound_submenu)

        # 8. Настройка звука окончания круга/раунда
        round_sound_submenu = tk.Menu(self.menu, tearoff=0)
        self.round_sound_var = tk.BooleanVar(value=initial_round_sound)
        round_sound_submenu.add_checkbutton(
            label="🔔 Звук окончания круга",
            variable=self.round_sound_var,
            command=on_toggle_round_sound
        )
        round_sound_submenu.add_separator()

        self.round_sound_type_var = tk.StringVar(value=initial_round_sound_type)
        for s_name in SOUND_PRESETS.keys():
            round_sound_submenu.add_radiobutton(
                label=s_name,
                variable=self.round_sound_type_var,
                value=s_name,
                command=lambda s=s_name: on_set_round_sound_type(s)
            )
        round_sound_submenu.add_radiobutton(
            label="Пользовательский (.wav)...",
            variable=self.round_sound_type_var,
            value="Пользовательский",
            command=on_choose_round_custom_sound
        )
        round_sound_submenu.add_separator()
        round_sound_submenu.add_command(label="▶ Прослушать звук", command=on_preview_round_sound)
        self.menu.add_cascade(label="🔁 Звук окончания круга", menu=round_sound_submenu)

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
