"""
Виджет отображения цифрового табло и обработка действий мыши.
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
        on_wheel: Callable[[int], None],
        on_reset: Callable[[], None],
        on_context_menu: Callable[[tk.Event], None],
        on_double_click: Callable[[], None],
    ):
        super().__init__(parent, bg=bg_color)
        self.parent = parent
        self.on_click = on_click
        self.on_drag_end = on_drag_end
        self.on_wheel = on_wheel
        self.on_reset = on_reset
        self.on_context_menu = on_context_menu
        self.on_double_click = on_double_click

        # Состояние перетаскивания
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_window_x = 0
        self.drag_window_y = 0
        self.is_dragging = False

        self.pack(expand=True, fill="both")
        self.create_widgets(bg_color, fg_color)
        self.bind_mouse_events()

    def create_widgets(self, bg: str, fg: str):
        # Цифровое табло (Consolas для четких моноширинных цифр)
        self.label = tk.Label(
            self,
            text="00:00:00",
            font=("Consolas", 52, "bold"),
            fg=fg,
            bg=bg,
            cursor="fleur"
        )
        self.label.pack(expand=True, fill="both", pady=(6, 2))

        # Нижняя подсказка / статус
        self.sub_label = tk.Label(
            self,
            text="ЛКМ: старт | ПКМ: меню",
            font=("Segoe UI", 8),
            fg="#6c7086",
            bg=bg
        )
        self.sub_label.pack(side="bottom", pady=(0, 4))

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

    def bind_mouse_events(self):
        widgets = [self, self.label, self.sub_label]
        for w in widgets:
            w.bind("<Enter>", self._on_enter)
            w.bind("<ButtonPress-1>", self._on_press)
            w.bind("<B1-Motion>", self._on_motion)
            w.bind("<ButtonRelease-1>", self._on_release)
            w.bind("<Button-2>", lambda e: self.on_reset())
            w.bind("<Button-3>", self._on_right_click)
            w.bind("<Double-Button-1>", lambda e: self.on_double_click())
            w.bind("<MouseWheel>", self._on_wheel)

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
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.drag_window_x = self.parent.winfo_x()
        self.drag_window_y = self.parent.winfo_y()
        self.is_dragging = False

    def _on_motion(self, event: tk.Event):
        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y
        if abs(dx) > 3 or abs(dy) > 3:
            self.is_dragging = True
            nx = self.drag_window_x + dx
            ny = self.drag_window_y + dy
            self.parent.geometry(f"+{nx}+{ny}")

    def _on_release(self, event: tk.Event):
        if self.is_dragging:
            self.on_drag_end()
        else:
            self.on_click()

    def _on_wheel(self, event: tk.Event):
        delta = 60 if event.delta > 0 else -60
        self.on_wheel(delta)
