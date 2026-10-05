"""
Виджет отображения цифрового табло:
- Динамическое масштабирование шрифта цифр при растягивании
- Растягивание окна за края и правый нижний угол
- Перемещение окна за тело виджета
- Отображение и подсказки
"""

import tkinter as tk
from typing import Callable


class TimerDisplay(tk.Frame):
    def __init__(
        self,
        parent: tk.Tk,
        bg_color: str,
        fg_color: str,
        on_click: Callable[[], None],
        on_drag_end: Callable[[], None],
        on_resize_end: Callable[[], None],
        on_wheel: Callable[[int], None],
        on_reset: Callable[[], None],
        on_context_menu: Callable[[tk.Event], None],
        on_double_click: Callable[[], None],
    ):
        super().__init__(parent, bg=bg_color)
        self.parent = parent
        self.on_click = on_click
        self.on_drag_end = on_drag_end
        self.on_resize_end = on_resize_end
        self.on_wheel = on_wheel
        self.on_reset = on_reset
        self.on_context_menu = on_context_menu
        self.on_double_click = on_double_click

        # Состояние перетаскивания и растягивания
        self.start_mouse_x = 0
        self.start_mouse_y = 0
        self.start_win_x = 0
        self.start_win_y = 0
        self.start_win_w = 0
        self.start_win_h = 0
        self.active_zone = "MOVE"
        self.action_performed = False

        self.pack(expand=True, fill="both")
        self.create_widgets(bg_color, fg_color)
        self.bind_mouse_events()

        # Слушатель изменения размера окна для масштабирования шрифта
        self.bind("<Configure>", self._on_configure)

    def create_widgets(self, bg: str, fg: str):
        # Цифровое табло (Consolas)
        self.label = tk.Label(
            self,
            text="00:00:00",
            font=("Consolas", 52, "bold"),
            fg=fg,
            bg=bg,
            cursor="fleur"
        )
        self.label.pack(expand=True, fill="both", pady=(4, 0))

        # Нижняя подсказка / статус
        self.sub_label = tk.Label(
            self,
            text="ЛКМ: старт | ПКМ: меню",
            font=("Segoe UI", 8),
            fg="#6c7086",
            bg=bg,
            cursor="fleur"
        )
        self.sub_label.pack(side="bottom", pady=(0, 3))

        # Визуальный уголок изменения размера в правом нижнем углу
        self.grip = tk.Label(
            self,
            text="◢",
            font=("Segoe UI", 9),
            fg="#5c5f77",
            bg=bg,
            cursor="size_nw_se"
        )
        self.grip.place(relx=1.0, rely=1.0, x=-2, y=-2, anchor="se")

    def _on_configure(self, event: tk.Event):
        """Плавное динамическое масштабирование шрифта под любой размер окна."""
        w, h = event.width, event.height
        if w < 60 or h < 30:
            return

        # Пропорциональный подбор размера шрифта
        font_size = max(18, min(int(h * 0.58), int(w / 5.2)))
        self.label.config(font=("Consolas", font_size, "bold"))

        sub_size = max(7, min(12, int(font_size / 5.2)))
        self.sub_label.config(font=("Segoe UI", sub_size))

    def update_time_text(self, text: str, fg: str = None):
        if fg:
            self.label.config(text=text, fg=fg)
        else:
            self.label.config(text=text)

    def set_status_text(self, text: str):
        self.sub_label.config(text=text)

    def update_colors(self, bg: str, fg: str):
        self.config(bg=bg)
        self.label.config(bg=bg, fg=fg)
        self.sub_label.config(bg=bg)
        self.grip.config(bg=bg)

    def bind_mouse_events(self):
        widgets = [self, self.label, self.sub_label, self.grip]
        for w in widgets:
            w.bind("<Enter>", self._on_enter)
            w.bind("<Motion>", self._on_mouse_hover)
            w.bind("<ButtonPress-1>", self._on_press)
            w.bind("<B1-Motion>", self._on_motion)
            w.bind("<ButtonRelease-1>", self._on_release)
            w.bind("<Button-2>", lambda e: self.on_reset())
            w.bind("<Button-3>", self._on_right_click)
            w.bind("<Double-Button-1>", lambda e: self.on_double_click())
            w.bind("<MouseWheel>", self._on_wheel)

    def _determine_zone(self, event: tk.Event) -> str:
        """Определяет, находится ли курсор в зоне растягивания или перемещения."""
        if event.widget == self.grip:
            return "SE"

        win_w = self.parent.winfo_width()
        win_h = self.parent.winfo_height()
        x_in_win = event.x_root - self.parent.winfo_x()
        y_in_win = event.y_root - self.parent.winfo_y()

        corner_margin = 16
        edge_margin = 8

        # Правый нижний угол
        if (win_w - x_in_win <= corner_margin) and (win_h - y_in_win <= corner_margin):
            return "SE"
        # Правый край
        elif win_w - x_in_win <= edge_margin:
            return "E"
        # Нижний край
        elif win_h - y_in_win <= edge_margin:
            return "S"
        # Перемещение всего окна
        return "MOVE"

    def _on_mouse_hover(self, event: tk.Event):
        """Динамическая смена курсора мыши при наведении на края/угол."""
        zone = self._determine_zone(event)
        cursor = "fleur"
        if zone == "SE":
            cursor = "size_nw_se"
        elif zone == "E":
            cursor = "size_we"
        elif zone == "S":
            cursor = "size_ns"

        try:
            event.widget.config(cursor=cursor)
        except Exception:
            pass

    def _on_enter(self, event: tk.Event):
        try:
            self.parent.focus_force()
        except Exception:
            pass

    def _on_right_click(self, event: tk.Event):
        try:
            self.parent.focus_force()
        except Exception:
            pass
        self.on_context_menu(event)

    def _on_press(self, event: tk.Event):
        try:
            self.parent.focus_force()
        except Exception:
            pass

        self.start_mouse_x = event.x_root
        self.start_mouse_y = event.y_root
        self.start_win_x = self.parent.winfo_x()
        self.start_win_y = self.parent.winfo_y()
        self.start_win_w = self.parent.winfo_width()
        self.start_win_h = self.parent.winfo_height()

        self.active_zone = self._determine_zone(event)
        self.action_performed = False

    def _on_motion(self, event: tk.Event):
        dx = event.x_root - self.start_mouse_x
        dy = event.y_root - self.start_mouse_y

        if abs(dx) > 3 or abs(dy) > 3:
            self.action_performed = True

            if self.active_zone == "SE":
                # Растягивание за угол (ширина и высота)
                new_w = max(180, self.start_win_w + dx)
                new_h = max(52, self.start_win_h + dy)
                self.parent.geometry(f"{new_w}x{new_h}")
            elif self.active_zone == "E":
                # Растягивание по горизонтали
                new_w = max(180, self.start_win_w + dx)
                self.parent.geometry(f"{new_w}x{self.start_win_h}")
            elif self.active_zone == "S":
                # Растягивание по вертикали
                new_h = max(52, self.start_win_h + dy)
                self.parent.geometry(f"{self.start_win_w}x{new_h}")
            else:
                # Перемещение окна
                nx = self.start_win_x + dx
                ny = self.start_win_y + dy
                self.parent.geometry(f"+{nx}+{ny}")

    def _on_release(self, event: tk.Event):
        if self.action_performed:
            if self.active_zone in ("SE", "E", "S"):
                self.on_resize_end()
            else:
                self.on_drag_end()
        else:
            self.on_click()

    def _on_wheel(self, event: tk.Event):
        delta = 60 if event.delta > 0 else -60
        self.on_wheel(delta)
