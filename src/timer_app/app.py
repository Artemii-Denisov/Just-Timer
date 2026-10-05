"""
Главный контроллер приложения таймера.
"""

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


class TimerApplication:
    def __init__(self, root: tk.Tk, config_path: Optional[str] = None):
        self.root = root
        self.config_manager = ConfigManager(config_path)

        # Инициализация ядра таймера
        initial_secs = self.config_manager.get("initial_time", 900)
        self.engine = TimerEngine(initial_duration=initial_secs)

        # Состояние анимации мигания
        self.flashing = False
        self.flash_step = 0

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

        # Автоматическая фокусировка при старте
        self.root.after(100, lambda: self.root.focus_force())

    def setup_window(self):
        self.root.title("Just Timer")
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
            on_exit=self.exit_app,
            initial_topmost=bool(self.config_manager.get("topmost", True)),
            initial_sound=bool(self.config_manager.get("sound_enabled", True)),
            initial_sound_type=self.config_manager.get("sound_type", "Дзынь (Ding)"),
            initial_transparent_bg=bool(self.config_manager.get("transparent_bg", False)),
            initial_global_hotkeys=bool(self.config_manager.get("global_hotkeys_enabled", True))
        )
        self.apply_current_colors()

    def bind_global_shortcuts(self):
        # Привязка на окно и на дисплей для мгновенной реакции
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
            self.display.set_status_text("▶ Таймер запущен")
            self._schedule_tick()
        else:
            self.display.set_status_text("⏸ Пауза (клик для продолжения)")

    def _schedule_tick(self):
        if not self.engine.is_running:
            return

        remaining, is_finished = self.engine.tick()
        show_hours = self.config_manager.get("show_hours", True)
        self.display.update_time_text(format_time(remaining, show_hours))

        if is_finished:
            self.display.set_status_text("✓ Время вышло!")
            self.trigger_finished()
        else:
            self.root.after(100, self._schedule_tick)

    def handle_reset(self):
        self.engine.reset()
        self.stop_flashing()
        show_hours = self.config_manager.get("show_hours", True)
        self.display.update_time_text(
            format_time(self.engine.remaining, show_hours),
            fg=self.config_manager.get("fg_color")
        )
        self.display.set_status_text("ЛКМ: старт | ПКМ: меню")

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
        new_duration = max(5.0, self.engine.initial_duration + delta_seconds)
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
        if self.config_manager.get("sound_enabled", True):
            sound_type = self.config_manager.get("sound_type", "Дзынь (Ding)")
            custom_path = self.config_manager.get("custom_sound_path", "")
            play_finish_sound(sound_type, custom_path)
        self.flash_alert()

    def flash_alert(self):
        if not self.flashing:
            return

        finish_color = self.config_manager.get("finish_color", "#ff3333")
        dim_color = "#666666"

        self.flash_step += 1
        current_fg = finish_color if (self.flash_step % 2 != 0) else dim_color
        self.display.label.config(fg=current_fg)

        if self.flash_step < 12:
            self.root.after(400, self.flash_alert)
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
