"""
Главный контроллер приложения таймера Just Timer.
"""

import sys
import os
import tkinter as tk
from tkinter import simpledialog, messagebox, colorchooser, filedialog
from typing import Optional

from .core.timer_engine import TimerEngine
from .config import ConfigManager
from .ui.display import TimerDisplay
from .ui.menu import TimerContextMenu
from .ui.themes import THEMES
from .utils.time_parser import parse_time_input, format_time
from .utils.sound import play_finish_sound, preview_sound, SOUND_PRESETS
from .utils.hotkeys import GlobalHotkeysManager

TRANSPARENT_COLOR_KEY = "#010101"


def get_asset_path(filename: str) -> str:
    """Возвращает путь к ресурсу assets/ для скрипта и собранного exe."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "assets", filename)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "assets", filename)


class TimerApplication:
    def __init__(self, root: tk.Tk, config_path: Optional[str] = None):
        self.root = root
        self.config_manager = ConfigManager(config_path)

        # Инициализация ядра таймера (с поддержкой кругов и интервалов)
        initial_secs = self.config_manager.get("initial_time", 900)
        total_rounds = int(self.config_manager.get("total_rounds", 1))
        rest_duration = float(self.config_manager.get("rest_duration", 0.0))

        self.engine = TimerEngine(
            initial_duration=initial_secs,
            total_rounds=total_rounds,
            rest_duration=rest_duration
        )

        # Состояние анимации мигания
        self.flashing = False
        self.flash_step = 0
        self.max_flash_steps = 12

        # Глобальные горячие клавиши (Ctrl+Alt+Space, Ctrl+Alt+R)
        self.hotkeys_manager = GlobalHotkeysManager(
            on_toggle=self.safe_global_toggle,
            on_reset=self.safe_global_reset
        )
        if self.config_manager.get("global_hotkeys_enabled", True):
            self.hotkeys_manager.start()

        self.setup_window()
        self.setup_ui()
        self.bind_global_shortcuts()

        # Первичное обновление отображения
        self.display.update_time_text(
            format_time(self.engine.remaining, self.config_manager.get("show_hours", True))
        )
        self.update_initial_status()

        # Автоматическая фокусировка при старте
        self.root.after(100, lambda: self.root.focus_force())

    def update_initial_status(self):
        """Отображение начального статуса в зависимости от режима."""
        if self.engine.total_rounds > 1:
            rest_str = f" (+{int(self.engine.rest_duration)}с отдых)" if self.engine.rest_duration > 0 else ""
            self.display.set_status_text(f"Круг 1/{self.engine.total_rounds}{rest_str} • Готов к старту")
        elif self.engine.total_rounds == 0:
            self.display.set_status_text("Режим: Бесконечный цикл • Готов к старту")
        else:
            self.display.set_status_text("ЛКМ: старт | ПКМ: меню")

    def setup_window(self):
        self.root.title("Just Timer")

        # Установка иконки приложения
        ico_path = get_asset_path("icon.ico")
        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass

        png_path = get_asset_path("icon.png")
        if os.path.exists(png_path):
            try:
                icon_img = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, icon_img)
                self._icon_ref = icon_img
            except Exception:
                pass

        self.root.overrideredirect(True)

        topmost = bool(self.config_manager.get("topmost", True))
        alpha = float(self.config_manager.get("alpha", 1.0))
        self.root.attributes("-topmost", topmost)
        self.root.attributes("-alpha", alpha)

        width = int(self.config_manager.get("window_width", 330))
        height = int(self.config_manager.get("window_height", 96))
        self.root.geometry(f"{width}x{height}")

        # Позиционирование окна
        wx = self.config_manager.get("window_x")
        wy = self.config_manager.get("window_y")
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        if wx is not None and wy is not None and 0 <= wx < screen_w and 0 <= wy < screen_h:
            self.root.geometry(f"+{wx}+{wy}")
        else:
            init_x = screen_w - width - 40
            init_y = 40
            self.root.geometry(f"+{init_x}+{init_y}")

    def setup_ui(self):
        bg = self.config_manager.get("bg_color", "#181825")
        fg = self.config_manager.get("fg_color", "#cdd6f4")
        self.root.configure(bg=bg)

        self.display = TimerDisplay(
            parent=self.root,
            bg_color=bg,
            fg_color=fg,
            on_click=self.handle_toggle,
            on_drag_end=self.handle_drag_end,
            on_resize_end=self.handle_resize_end,
            on_wheel=self.handle_wheel,
            on_reset=self.handle_reset,
            on_context_menu=self.handle_context_menu,
            on_double_click=self.handle_custom_time
        )

        self.context_menu = TimerContextMenu(
            parent=self.root,
            on_toggle=self.handle_toggle,
            on_reset=self.handle_reset,
            on_set_duration=self.handle_set_duration,
            on_custom_time=self.handle_custom_time,
            on_set_theme=self.handle_set_theme,
            on_choose_fg=self.handle_choose_fg,
            on_choose_bg=self.handle_choose_bg,
            on_choose_finish=self.handle_choose_finish,
            on_set_alpha=self.handle_set_alpha,
            on_toggle_transparent_bg=self.handle_toggle_transparent_bg,
            on_toggle_topmost=self.handle_toggle_topmost,
            on_toggle_sound=self.handle_toggle_sound,
            on_set_sound_type=self.handle_set_sound_type,
            on_choose_custom_sound=self.handle_choose_custom_sound,
            on_preview_sound=self.handle_preview_sound,
            on_toggle_global_hotkeys=self.handle_toggle_global_hotkeys,
            on_set_rounds=self.handle_set_rounds,
            on_custom_rounds=self.handle_custom_rounds,
            on_toggle_infinite_loop=self.handle_toggle_infinite_loop,
            on_exit=self.exit_app,
            initial_topmost=bool(self.config_manager.get("topmost", True)),
            initial_sound=bool(self.config_manager.get("sound_enabled", True)),
            initial_sound_type=self.config_manager.get("sound_type", "Дзынь (Ding)"),
            initial_transparent_bg=bool(self.config_manager.get("transparent_bg", False)),
            initial_global_hotkeys=bool(self.config_manager.get("global_hotkeys_enabled", True))
        )
        self.apply_current_colors()

    def bind_global_shortcuts(self):
        for target in [self.root, self.display, self.display.label, self.display.sub_label]:
            target.bind("<space>", lambda e: self.handle_toggle())
            target.bind("<r>", lambda e: self.handle_reset())
            target.bind("<R>", lambda e: self.handle_reset())
            target.bind("<Escape>", lambda e: self.exit_app())
            target.bind("<Control-q>", lambda e: self.exit_app())
            target.bind("<Control-Q>", lambda e: self.exit_app())
            target.bind("<t>", lambda e: self.toggle_topmost_key())
            target.bind("<T>", lambda e: self.toggle_topmost_key())

    # === БЕЗОПАСНЫЕ ОБРАБОТЧИКИ ГЛОБАЛЬНЫХ КЛАВИШ ===
    def safe_global_toggle(self):
        self.root.after(0, self.handle_toggle)

    def safe_global_reset(self):
        self.root.after(0, self.handle_reset)

    # === ОБРАБОТЧИКИ СОБЫТИЙ ТАЙМЕРА ===
    def handle_toggle(self):
        if self.flashing:
            self.stop_flashing()
            self.handle_reset()
            return

        is_running = self.engine.toggle()
        if is_running:
            self.update_running_status()
            self._schedule_tick()
        else:
            if self.engine.total_rounds > 1:
                self.display.set_status_text(f"⏸ Пауза (Круг {self.engine.current_round}/{self.engine.total_rounds})")
            elif self.engine.total_rounds == 0:
                self.display.set_status_text(f"⏸ Пауза (Круг {self.engine.current_round}/∞)")
            else:
                self.display.set_status_text("⏸ Пауза (клик для продолжения)")

    def update_running_status(self):
        """Обновляет строку статуса при работающем таймере."""
        if self.engine.total_rounds > 1:
            if self.engine.is_rest:
                next_round = min(self.engine.total_rounds, self.engine.current_round + 1)
                self.display.set_status_text(f"☕ Отдых (перед кругом {next_round}/{self.engine.total_rounds})")
            else:
                self.display.set_status_text(f"▶ Круг {self.engine.current_round}/{self.engine.total_rounds} • Работа")
        elif self.engine.total_rounds == 0:
            if self.engine.is_rest:
                self.display.set_status_text(f"☕ Отдых (перед кругом {self.engine.current_round + 1}/∞)")
            else:
                self.display.set_status_text(f"▶ Круг {self.engine.current_round}/∞ • Автоповтор")
        else:
            self.display.set_status_text("▶ Таймер запущен")

    def _schedule_tick(self):
        if not self.engine.is_running:
            return

        remaining, is_event = self.engine.tick()
        show_hours = self.config_manager.get("show_hours", True)
        self.display.update_time_text(format_time(remaining, show_hours))

        # Обновление строчки статуса
        self.update_running_status()

        if is_event:
            ev = self.engine.last_event
            if ev in ("round_next", "round_rest"):
                # Звуковой сигнал завершения круга / начала отдыха
                if self.config_manager.get("sound_enabled", True):
                    sound_type = self.config_manager.get("sound_type", "Дзынь (Ding)")
                    custom_path = self.config_manager.get("custom_sound_path", "")
                    play_finish_sound(sound_type, custom_path)
                self.flash_alert(max_steps=4)
                self.root.after(100, self._schedule_tick)
                return

            elif ev == "all_finished":
                # Все круги завершены!
                if self.engine.total_rounds > 1:
                    t = self.engine.total_rounds
                    self.display.set_status_text(f"✓ Все {t} кругов завершены!")
                else:
                    self.display.set_status_text("✓ Время вышло!")
                self.trigger_finished()
                return

        self.root.after(100, self._schedule_tick)

    def handle_reset(self):
        self.engine.reset()
        self.stop_flashing()
        show_hours = self.config_manager.get("show_hours", True)
        self.display.update_time_text(
            format_time(self.engine.remaining, show_hours),
            fg=self.config_manager.get("fg_color")
        )
        self.update_initial_status()

    def handle_set_duration(self, seconds: int):
        self.stop_flashing()
        self.engine.set_duration(seconds)
        self.config_manager.set("initial_time", seconds)
        self.config_manager.save()

        show_hours = self.config_manager.get("show_hours", True)
        self.display.update_time_text(format_time(self.engine.remaining, show_hours))

        if self.engine.is_running:
            self._schedule_tick()
        else:
            self.display.set_status_text(f"Установлено: {format_time(seconds, show_hours)}")

    # === РЕЖИМ КРУГОВ И ИНТЕРВАЛОВ ===
    def handle_set_rounds(self, total_rounds: int, work_duration: float, rest_duration: float = 0.0):
        self.stop_flashing()
        self.engine.set_rounds_mode(total_rounds, work_duration, rest_duration)
        self.config_manager.set("total_rounds", total_rounds)
        self.config_manager.set("initial_time", int(work_duration))
        self.config_manager.set("rest_duration", int(rest_duration))
        self.config_manager.save()

        show_hours = self.config_manager.get("show_hours", True)
        self.display.update_time_text(format_time(self.engine.remaining, show_hours))

        if total_rounds > 1:
            rest_str = f" (+{int(rest_duration)}с отдых)" if rest_duration > 0 else ""
            self.display.set_status_text(f"Режим: {total_rounds} кругов по {format_time(work_duration, False)}{rest_str}")
        elif total_rounds == 0:
            self.display.set_status_text(f"Режим: Бесконечный цикл по {format_time(work_duration, False)}")
        else:
            self.display.set_status_text(f"Установлено: {format_time(work_duration, show_hours)}")

        if self.engine.is_running:
            self._schedule_tick()

    def handle_custom_rounds(self):
        # 1. Запрос количества кругов
        count_str = simpledialog.askstring(
            "Настройка кругов",
            "Количество кругов:\n(Например: 5, или 0 для бесконечного автоповтора)",
            parent=self.root
        )
        if count_str is None:
            return
        try:
            total_rounds = int(count_str.strip())
            if total_rounds < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Ошибка ввода", "Укажите целое число (0, 1, 2...).", parent=self.root)
            return

        # 2. Время одного круга
        time_str = simpledialog.askstring(
            "Время круга",
            "Длительность одного круга:\n(Например: '30s', '1m', '45', '10:00')",
            parent=self.root
        )
        if time_str is None:
            return
        work_sec = parse_time_input(time_str)
        if not work_sec or work_sec <= 0:
            messagebox.showwarning("Ошибка ввода", "Не удалось распознать время круга.", parent=self.root)
            return

        # 3. Время отдыха между кругами
        rest_sec = 0
        if total_rounds != 1:
            rest_str = simpledialog.askstring(
                "Отдых между кругами",
                "Время отдыха между кругами (сек):\n(Оставьте 0, если отдых не нужен)",
                initialvalue="0",
                parent=self.root
            )
            if rest_str:
                parsed_rest = parse_time_input(rest_str)
                if parsed_rest is not None and parsed_rest >= 0:
                    rest_sec = parsed_rest

        self.handle_set_rounds(total_rounds, work_sec, rest_sec)

    def handle_toggle_infinite_loop(self):
        if self.engine.total_rounds == 0:
            self.handle_set_rounds(1, self.engine.work_duration, 0)
        else:
            self.handle_set_rounds(0, self.engine.work_duration, self.engine.rest_duration)

    def handle_custom_time(self):
        prompt = "Введите время:\nНапример: '15' (15 мин), '10:30', '1h 30m', '45s'"
        res = simpledialog.askstring("Задать время", prompt, parent=self.root)
        if res:
            parsed = parse_time_input(res)
            if parsed and parsed > 0:
                self.handle_set_duration(parsed)
            else:
                messagebox.showwarning("Ошибка ввода", "Не удалось распознать формат времени.", parent=self.root)

    def handle_wheel(self, delta_seconds: int):
        if self.engine.is_running:
            return
        new_duration = max(5.0, self.engine.work_duration + delta_seconds)
        self.handle_set_duration(int(new_duration))

    def handle_drag_end(self):
        self.config_manager.set("window_x", self.root.winfo_x())
        self.config_manager.set("window_y", self.root.winfo_y())
        self.config_manager.save()

    def handle_resize_end(self):
        self.config_manager.set("window_width", self.root.winfo_width())
        self.config_manager.set("window_height", self.root.winfo_height())
        self.config_manager.save()

    def handle_context_menu(self, event: tk.Event):
        self.context_menu.show(event.x_root, event.y_root)

    # === ЗАВЕРШЕНИЕ И СИГНАЛЫ ===
    def trigger_finished(self):
        self.flashing = True
        self.flash_step = 0
        self.max_flash_steps = 12
        if self.config_manager.get("sound_enabled", True):
            sound_type = self.config_manager.get("sound_type", "Дзынь (Ding)")
            custom_path = self.config_manager.get("custom_sound_path", "")
            play_finish_sound(sound_type, custom_path)
        self.flash_alert()

    def flash_alert(self, max_steps: int = 12):
        if not self.flashing:
            self.flashing = True
            self.flash_step = 0
            self.max_flash_steps = max_steps

        finish_color = self.config_manager.get("finish_color", "#ff3333")
        dim_color = "#666666"

        self.flash_step += 1
        current_fg = finish_color if (self.flash_step % 2 != 0) else dim_color
        self.display.label.config(fg=current_fg)

        if self.flash_step < self.max_flash_steps:
            self.root.after(350, lambda: self.flash_alert(self.max_flash_steps))
        else:
            self.display.label.config(fg=finish_color)
            self.flashing = False

    def stop_flashing(self):
        self.flashing = False
        fg = self.config_manager.get("fg_color", "#cdd6f4")
        self.display.label.config(fg=fg)

    # === НАСТРОЙКИ ЗВУКА ===
    def handle_set_sound_type(self, sound_type: str):
        self.config_manager.set("sound_type", sound_type)
        self.config_manager.save()
        preview_sound(sound_type, self.config_manager.get("custom_sound_path"))

    def handle_choose_custom_sound(self):
        path = filedialog.askopenfilename(
            title="Выберите звуковой файл (.wav)",
            filetypes=[("WAV Audio", "*.wav"), ("Все файлы", "*.*")],
            parent=self.root
        )
        if path:
            self.config_manager.set("sound_type", "Пользовательский")
            self.config_manager.set("custom_sound_path", path)
            self.context_menu.sound_type_var.set("Пользовательский")
            self.config_manager.save()
            preview_sound("Пользовательский", path)

    def handle_preview_sound(self):
        sound_type = self.context_menu.sound_type_var.get()
        custom_path = self.config_manager.get("custom_sound_path", "")
        preview_sound(sound_type, custom_path)

    def handle_toggle_global_hotkeys(self):
        val = self.context_menu.global_hotkeys_var.get()
        self.config_manager.set("global_hotkeys_enabled", val)
        self.config_manager.save()
        if val:
            self.hotkeys_manager.start()
        else:
            self.hotkeys_manager.stop()

    # === НАСТРОЙКИ ОФОРМЛЕНИЯ ===
    def apply_current_colors(self):
        is_transparent = bool(self.config_manager.get("transparent_bg", False))
        fg = self.config_manager.get("fg_color", "#cdd6f4")
        if is_transparent:
            bg = TRANSPARENT_COLOR_KEY
            self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR_KEY)
        else:
            bg = self.config_manager.get("bg_color", "#181825")
            self.root.wm_attributes("-transparentcolor", "")
        self.root.configure(bg=bg)
        self.display.update_colors(bg, fg)

    def handle_toggle_transparent_bg(self):
        val = self.context_menu.transparent_bg_var.get()
        self.config_manager.set("transparent_bg", val)
        self.apply_current_colors()
        self.config_manager.save()

    def handle_set_theme(self, theme_name: str):
        if theme_name in THEMES:
            t = THEMES[theme_name]
            self.config_manager.set("theme", theme_name)
            self.config_manager.set("bg_color", t["bg"])
            self.config_manager.set("fg_color", t["fg"])
            self.config_manager.set("finish_color", t["finish"])
            self.apply_current_colors()
            self.config_manager.save()

    def handle_choose_fg(self):
        color = colorchooser.askcolor(
            color=self.config_manager.get("fg_color"),
            title="Выберите цвет цифр",
            parent=self.root
        )
        if color and color[1]:
            self.config_manager.set("fg_color", color[1])
            self.config_manager.set("theme", "Пользовательская")
            self.apply_current_colors()
            self.config_manager.save()

    def handle_choose_bg(self):
        color = colorchooser.askcolor(
            color=self.config_manager.get("bg_color"),
            title="Выберите цвет фона",
            parent=self.root
        )
        if color and color[1]:
            self.config_manager.set("bg_color", color[1])
            self.config_manager.set("theme", "Пользовательская")
            self.apply_current_colors()
            self.config_manager.save()

    def handle_choose_finish(self):
        color = colorchooser.askcolor(
            color=self.config_manager.get("finish_color"),
            title="Выберите цвет окончания",
            parent=self.root
        )
        if color and color[1]:
            self.config_manager.set("finish_color", color[1])
            self.config_manager.save()

    def handle_set_alpha(self, alpha_val: float):
        self.config_manager.set("alpha", alpha_val)
        self.root.attributes("-alpha", alpha_val)
        self.config_manager.save()

    def handle_toggle_topmost(self):
        val = self.context_menu.topmost_var.get()
        self.config_manager.set("topmost", val)
        self.root.attributes("-topmost", val)
        self.config_manager.save()

    def toggle_topmost_key(self):
        new_val = not self.context_menu.topmost_var.get()
        self.context_menu.topmost_var.set(new_val)
        self.handle_toggle_topmost()

    def handle_toggle_sound(self):
        val = self.context_menu.sound_var.get()
        self.config_manager.set("sound_enabled", val)
        self.config_manager.save()

    def exit_app(self, event=None):
        if hasattr(self, 'hotkeys_manager'):
            self.hotkeys_manager.stop()
        self.config_manager.set("window_x", self.root.winfo_x())
        self.config_manager.set("window_y", self.root.winfo_y())
        self.config_manager.set("window_width", self.root.winfo_width())
        self.config_manager.set("window_height", self.root.winfo_height())
        self.config_manager.save()
        self.root.destroy()
