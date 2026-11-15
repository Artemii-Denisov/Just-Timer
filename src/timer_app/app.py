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
from .utils.sound import play_finish_sound, play_round_sound, preview_sound, SOUND_PRESETS
from .utils.hotkeys import GlobalHotkeysManager

APP_USER_MODEL_ID = "Denis.JustTimer.App.1.0"
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

        # Состояние анимации мигания и планировщика тиков
        self.flashing = False
        self.flash_step = 0
        self.max_flash_steps = 12
        self._restore_fg_at_end = False
        self._tick_job: Optional[str] = None
        self._flash_job: Optional[str] = None

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
        try:
            self.root.attributes("-topmost", topmost)
        except tk.TclError:
            pass
        try:
            self.root.attributes("-alpha", alpha)
        except tk.TclError:
            pass

        width = int(self.config_manager.get("window_width", 330))
        height = int(self.config_manager.get("window_height", 96))
        self.root.geometry(f"{width}x{height}")

        # Отображение окна на панели задач Windows для безрамочного окна (overrideredirect)
        self.setup_taskbar_presence(ico_path)

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

    def setup_taskbar_presence(self, ico_path: str):
        """Гарантирует отображение безрамочного окна на панели задач Windows с правильной иконкой."""
        if sys.platform != "win32":
            return

        try:
            import ctypes
            # Устанавливаем уникальный AppUserModelID, чтобы Windows группировала окно отдельно с его иконкой
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)

            def _apply_taskbar_style():
                try:
                    hwnd = self.root.winfo_id()
                    parent_hwnd = ctypes.windll.user32.GetParent(hwnd)
                    target_hwnd = parent_hwnd if parent_hwnd else hwnd

                    GWL_EXSTYLE = -20
                    WS_EX_APPWINDOW = 0x00040000
                    WS_EX_TOOLWINDOW = 0x00000080

                    style = ctypes.windll.user32.GetWindowLongW(target_hwnd, GWL_EXSTYLE)
                    style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
                    ctypes.windll.user32.SetWindowLongW(target_hwnd, GWL_EXSTYLE, style)

                    # Устанавливаем иконку окна в заголовке/панели задач через Win32 WM_SETICON
                    if os.path.exists(ico_path):
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010

                        hicon_big = ctypes.windll.user32.LoadImageW(
                            None, ico_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE
                        )
                        hicon_small = ctypes.windll.user32.LoadImageW(
                            None, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE
                        )
                        if hicon_big:
                            ctypes.windll.user32.SendMessageW(target_hwnd, WM_SETICON, ICON_BIG, hicon_big)
                        if hicon_small:
                            ctypes.windll.user32.SendMessageW(target_hwnd, WM_SETICON, ICON_SMALL, hicon_small)
                except Exception:
                    pass

            self.root.after(10, _apply_taskbar_style)
        except Exception:
            pass

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
        show_status = bool(self.config_manager.get("show_status", True))
        self.display.set_show_status(show_status)

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
            on_toggle_status=self.handle_toggle_status,
            on_toggle_topmost=self.handle_toggle_topmost,
            on_toggle_sound=self.handle_toggle_sound,
            on_set_sound_type=self.handle_set_sound_type,
            on_choose_custom_sound=self.handle_choose_custom_sound,
            on_preview_sound=self.handle_preview_sound,
            on_toggle_round_sound=self.handle_toggle_round_sound,
            on_set_round_sound_type=self.handle_set_round_sound_type,
            on_choose_round_custom_sound=self.handle_choose_round_custom_sound,
            on_preview_round_sound=self.handle_preview_round_sound,
            on_toggle_global_hotkeys=self.handle_toggle_global_hotkeys,
            on_set_rounds=self.handle_set_rounds,
            on_custom_rounds=self.handle_custom_rounds,
            on_toggle_infinite_loop=self.handle_toggle_infinite_loop,
            on_exit=self.exit_app,
            initial_topmost=bool(self.config_manager.get("topmost", True)),
            initial_sound=bool(self.config_manager.get("sound_enabled", True)),
            initial_sound_type=self.config_manager.get("sound_type", "Дзынь (Ding)"),
            initial_round_sound=bool(self.config_manager.get("round_sound_enabled", True)),
            initial_round_sound_type=self.config_manager.get("round_sound_type", "Короткий сигнал (Beep)"),
            initial_transparent_bg=bool(self.config_manager.get("transparent_bg", False)),
            initial_show_status=show_status,
            initial_global_hotkeys=bool(self.config_manager.get("global_hotkeys_enabled", True))
        )
        self.apply_current_colors()

    def bind_global_shortcuts(self):
        for target in (self.root, self.display, self.display.canvas):
            target.bind("<KeyPress>", self._on_key_press)

    def _on_key_press(self, event: tk.Event):
        """Обработка горячих клавиш независимо от раскладки клавиатуры."""
        ctrl = (event.state & 0x4) != 0
        is_win = sys.platform == "win32"
        keysym_l = event.keysym.lower() if event.keysym else ""
        char_l = event.char.lower() if event.char else ""

        if event.keysym == "Escape" or (is_win and event.keycode == 27):
            self.exit_app()
            return "break"

        if ctrl and (
            (is_win and event.keycode == 81)
            or keysym_l in ("q", "cyrillic_shorti")
            or char_l in ("q", "й", "\x11")
        ):
            self.exit_app()
            return "break"

        if event.keysym == "space" or (is_win and event.keycode == 32):
            self.handle_toggle()
            return "break"

        if not ctrl and (
            (is_win and event.keycode == 82)
            or keysym_l in ("r", "cyrillic_ka")
            or char_l in ("r", "к")
        ):
            self.handle_reset()
            return "break"

        if not ctrl and (
            (is_win and event.keycode == 84)
            or keysym_l in ("t", "cyrillic_ie")
            or char_l in ("t", "е")
        ):
            self.toggle_topmost_key()
            return "break"

        if not ctrl and (
            (is_win and event.keycode == 83)
            or keysym_l in ("s", "cyrillic_yeru")
            or char_l in ("s", "ы")
        ):
            self.toggle_status_key()
            return "break"

    # === БЕЗОПАСНЫЕ ОБРАБОТЧИКИ ГЛОБАЛЬНЫХ КЛАВИШ ===
    def safe_global_toggle(self):
        self.root.after(0, self.handle_toggle)

    def safe_global_reset(self):
        self.root.after(0, self.handle_reset)

    # === ОБРАБОТЧИКИ СОБЫТИЙ ТАЙМЕРА ===
    def _cancel_tick(self):
        if self._tick_job is not None:
            try:
                self.root.after_cancel(self._tick_job)
            except Exception:
                pass
            self._tick_job = None

    def _start_tick(self):
        self._cancel_tick()
        self._tick_job = self.root.after(100, self._schedule_tick)

    def handle_toggle(self):
        if self.flashing:
            self.stop_flashing()
            self.handle_reset()
            return

        is_running = self.engine.toggle()
        if is_running:
            self.update_running_status()
            self._start_tick()
        else:
            self._cancel_tick()
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
        self._tick_job = None
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
                if self.config_manager.get("round_sound_enabled", True):
                    round_sound_type = self.config_manager.get("round_sound_type", "Короткий сигнал (Beep)")
                    custom_path = self.config_manager.get("round_custom_sound_path", "")
                    play_round_sound(round_sound_type, custom_path)
                self.start_flashing(max_steps=4, restore_fg_at_end=True)
                self._tick_job = self.root.after(100, self._schedule_tick)
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

        self._tick_job = self.root.after(100, self._schedule_tick)

    def handle_reset(self):
        self._cancel_tick()
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
            self._start_tick()
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
            self._start_tick()

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
        if self.engine.work_duration < 60 or (self.engine.work_duration == 60 and delta_seconds < 0):
            step = 10 if delta_seconds > 0 else -10
        else:
            step = 60 if delta_seconds > 0 else -60

        new_duration = max(5.0, self.engine.work_duration + step)
        self.stop_flashing()
        self.engine.set_duration(new_duration)
        self.config_manager.set("initial_time", int(new_duration))
        self.config_manager.save()

        show_hours = self.config_manager.get("show_hours", True)
        self.display.update_time_text(format_time(self.engine.remaining, show_hours))

        if self.engine.total_rounds != 1:
            self.update_initial_status()
        else:
            self.display.set_status_text(f"Установлено: {format_time(new_duration, show_hours)}")

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
        if self.config_manager.get("sound_enabled", True):
            sound_type = self.config_manager.get("sound_type", "Дзынь (Ding)")
            custom_path = self.config_manager.get("custom_sound_path", "")
            play_finish_sound(sound_type, custom_path)
        self.start_flashing(max_steps=12, restore_fg_at_end=False)

    def start_flashing(self, max_steps: int = 12, restore_fg_at_end: bool = False):
        if self._flash_job is not None:
            try:
                self.root.after_cancel(self._flash_job)
            except Exception:
                pass
            self._flash_job = None

        self.flashing = True
        self.flash_step = 0
        self.max_flash_steps = max_steps
        self._restore_fg_at_end = restore_fg_at_end
        self._flash_tick()

    def _flash_tick(self):
        self._flash_job = None
        if not self.flashing:
            return

        finish_color = self.config_manager.get("finish_color", "#ff3333")
        dim_color = "#666666"

        self.flash_step += 1
        current_fg = finish_color if (self.flash_step % 2 != 0) else dim_color
        self.display.set_digit_color(current_fg)

        if self.flash_step < self.max_flash_steps:
            self._flash_job = self.root.after(350, self._flash_tick)
        else:
            self.flashing = False
            if self._restore_fg_at_end or self.engine.is_running:
                fg = self.config_manager.get("fg_color", "#cdd6f4")
                self.display.set_digit_color(fg)
            else:
                self.display.set_digit_color(finish_color)

    def flash_alert(self, max_steps: int = 12):
        self.start_flashing(max_steps=max_steps, restore_fg_at_end=False)

    def stop_flashing(self):
        self.flashing = False
        if self._flash_job is not None:
            try:
                self.root.after_cancel(self._flash_job)
            except Exception:
                pass
            self._flash_job = None
        fg = self.config_manager.get("fg_color", "#cdd6f4")
        self.display.set_digit_color(fg)

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

    def handle_toggle_round_sound(self):
        val = self.context_menu.round_sound_var.get()
        self.config_manager.set("round_sound_enabled", val)
        self.config_manager.save()

    def handle_set_round_sound_type(self, sound_type: str):
        self.config_manager.set("round_sound_type", sound_type)
        self.config_manager.save()
        preview_sound(sound_type, self.config_manager.get("round_custom_sound_path"))

    def handle_choose_round_custom_sound(self):
        path = filedialog.askopenfilename(
            title="Выберите звуковой файл окончания круга (.wav)",
            filetypes=[("WAV Audio", "*.wav"), ("Все файлы", "*.*")],
            parent=self.root
        )
        if path:
            self.config_manager.set("round_sound_type", "Пользовательский")
            self.config_manager.set("round_custom_sound_path", path)
            self.context_menu.round_sound_type_var.set("Пользовательский")
            self.config_manager.save()
            preview_sound("Пользовательский", path)

    def handle_preview_round_sound(self):
        sound_type = self.context_menu.round_sound_type_var.get()
        custom_path = self.config_manager.get("round_custom_sound_path", "")
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
    @staticmethod
    def _compute_transparent_colors(fg_color: str):
        """Выбирает контрастный цвет обводки и смежный хромакей без ореола ClearType."""
        lum = 1.0
        if fg_color and fg_color.startswith("#") and len(fg_color) == 7:
            try:
                r = int(fg_color[1:3], 16)
                g = int(fg_color[3:5], 16)
                b = int(fg_color[5:7], 16)
                lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            except ValueError:
                pass
        if lum > 0.35:
            return "#181824", "#181825"
        return "#f0f0f4", "#f0f0f5"

    def apply_current_colors(self):
        is_transparent = bool(self.config_manager.get("transparent_bg", False))
        fg = self.config_manager.get("fg_color", "#cdd6f4")
        if is_transparent:
            chroma_key, outline_color = self._compute_transparent_colors(fg)
            bg = chroma_key
            try:
                self.root.wm_attributes("-transparentcolor", chroma_key)
            except tk.TclError:
                # На Linux -transparentcolor не поддерживается; используем полупрозрачный HUD-фон
                bg = outline_color
                try:
                    self.root.attributes("-alpha", min(float(self.config_manager.get("alpha", 1.0)), 0.78))
                except tk.TclError:
                    pass
            self.root.configure(bg=bg)
            self.display.update_colors(bg, fg, transparent_mode=True, outline_color=outline_color)
        else:
            bg = self.config_manager.get("bg_color", "#181825")
            try:
                self.root.wm_attributes("-transparentcolor", "")
            except tk.TclError:
                pass
            try:
                self.root.attributes("-alpha", float(self.config_manager.get("alpha", 1.0)))
            except tk.TclError:
                pass
            self.root.configure(bg=bg)
            self.display.update_colors(bg, fg, transparent_mode=False)

    def handle_toggle_transparent_bg(self):
        val = self.context_menu.transparent_bg_var.get()
        self.config_manager.set("transparent_bg", val)
        self.apply_current_colors()
        self.config_manager.save()

    def handle_toggle_status(self):
        val = bool(self.context_menu.show_status_var.get())
        self.config_manager.set("show_status", val)
        self.display.set_show_status(val)
        self.config_manager.save()

    def toggle_status_key(self):
        new_val = not self.context_menu.show_status_var.get()
        self.context_menu.show_status_var.set(new_val)
        self.handle_toggle_status()

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
        try:
            self.root.attributes("-alpha", alpha_val)
        except tk.TclError:
            pass
        self.config_manager.save()

    def handle_toggle_topmost(self):
        val = self.context_menu.topmost_var.get()
        self.config_manager.set("topmost", val)
        try:
            self.root.attributes("-topmost", val)
        except tk.TclError:
            pass
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
        self._cancel_tick()
        if self._flash_job is not None:
            try:
                self.root.after_cancel(self._flash_job)
            except Exception:
                pass
            self._flash_job = None
        if hasattr(self, 'hotkeys_manager'):
            self.hotkeys_manager.stop()
        self.config_manager.set("window_x", self.root.winfo_x())
        self.config_manager.set("window_y", self.root.winfo_y())
        self.config_manager.set("window_width", self.root.winfo_width())
        self.config_manager.set("window_height", self.root.winfo_height())
        self.config_manager.save()
        self.root.destroy()
