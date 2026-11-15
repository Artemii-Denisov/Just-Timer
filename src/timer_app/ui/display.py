"""
Виджет отображения цифрового табло на базе Canvas:
- Точное масштабирование шрифта в пикселях без обрезания цифр и статусной строки
- Контрастная обводка цифр в прозрачном HUD-режиме (читается на любом фоне)
- Растягивание окна за все 4 края и 4 угла + перетаскивание за тело виджета
- Корректное разделение клика, перетаскивания и двойного клика
"""

import re
import sys
import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Optional, Tuple


OUTLINE_OFFSETS_MAIN = (
    (-1, -1), (0, -1), (1, -1),
    (-1, 0),           (1, 0),
    (-1, 1),  (0, 1),  (1, 1),
    (-2, 0),  (2, 0),  (0, -2), (0, 2),
)

OUTLINE_OFFSETS_STATUS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
)


def _is_light_hex(color: str) -> bool:
    """Возвращает True, если hex-цвет светлый."""
    if not color or not color.startswith("#") or len(color) != 7:
        return False
    try:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        return lum > 0.5
    except ValueError:
        return False


def _pick_font_family(candidates: Tuple[str, ...], fallback: str) -> str:
    """Выбирает первый доступный в системе шрифт из списка кандидатов."""
    try:
        available = set(tkfont.families())
        for name in candidates:
            if name in available:
                return name
    except Exception:
        pass
    return fallback


class TimerDisplay(tk.Frame):
    MIN_WIDTH = 160
    MIN_HEIGHT = 44

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

        self.pack_propagate(False)

        # Состояние отображения
        self._time_text: str = "00:00:00"
        self._status_text: str = "ЛКМ: старт | ПКМ: меню"
        self._show_status: bool = True
        self._bg_color: str = bg_color
        self._fg_color: str = fg_color
        self._digit_color: str = fg_color
        self._transparent_mode: bool = False
        self._outline_color: str = "#181825"

        # Кроссплатформенный выбор шрифтов
        self.digit_font_family = _pick_font_family(
            ("Consolas", "DejaVu Sans Mono", "Liberation Mono", "Ubuntu Mono", "Courier New"),
            "TkFixedFont",
        )
        self.ui_font_family = _pick_font_family(
            ("Segoe UI", "Ubuntu", "DejaVu Sans", "Liberation Sans"),
            "TkDefaultFont",
        )

        self._digit_font = tkfont.Font(family=self.digit_font_family, size=-40, weight="bold")
        self._status_font = tkfont.Font(family=self.ui_font_family, size=-11)
        self._grip_font = tkfont.Font(family=self.ui_font_family, size=-11)
        self._measure_digit_font = tkfont.Font(family=self.digit_font_family, size=-40, weight="bold")
        self._measure_status_font = tkfont.Font(family=self.ui_font_family, size=-11)
        self._cur_digit_px: int = 40
        self._cur_status_px: int = 11
        self._cur_grip_px: int = 11
        self._current_cursor: str = "fleur"

        # Кэш подбора размеров шрифта чтобы не пересчитывать на каждом тике
        self._cached_layout_key: Optional[Tuple[int, int, str, str, bool]] = None
        self._cached_sizes: Tuple[int, int, int] = (40, 11, 20)

        # Состояние перетаскивания, растягивания и кликов
        self.start_mouse_x = 0
        self.start_mouse_y = 0
        self.start_win_x = 0
        self.start_win_y = 0
        self.start_win_w = 0
        self.start_win_h = 0
        self.active_zone = "MOVE"
        self.action_performed = False
        self._click_job: Optional[str] = None
        self._double_click_flag = False

        self.pack(expand=True, fill="both")
        self.create_widgets(bg_color)
        self.bind_mouse_events()

        self.canvas.bind("<Configure>", self._on_configure)

    def create_widgets(self, bg: str):
        self.canvas = tk.Canvas(
            self,
            bg=bg,
            highlightthickness=0,
            bd=0,
            cursor="fleur",
        )
        self.canvas.pack(expand=True, fill="both")

    def _compute_layout(self, w: int, h: int) -> Tuple[int, int, int]:
        """Рассчитывает размеры шрифтов в пикселях и высоту нижней полосы статуса."""
        base_text = self._time_text if len(self._time_text) >= 5 else "00:00:00"
        sample = re.sub(r"\d", "8", base_text)
        status_part = self._status_text if self._show_status else ""
        layout_key = (w, h, sample, status_part, self._show_status)
        if self._cached_layout_key == layout_key:
            return self._cached_sizes

        if self._show_status:
            status_band_h = max(18, min(30, int(h * 0.22)))
            avail_h = max(24, h - status_band_h - 8)
        else:
            status_band_h = 0
            avail_h = max(24, h - 10)
        avail_w = max(60, w - 24)

        px_size = max(14, int(avail_h * 0.85))
        self._measure_digit_font.configure(size=-px_size)
        m_w = self._measure_digit_font.measure(sample)
        m_h = self._measure_digit_font.metrics("linespace")

        if m_w > avail_w or m_h > avail_h:
            scale = min(avail_w / max(1, m_w), avail_h / max(1, m_h))
            px_size = max(12, int(px_size * scale))
            self._measure_digit_font.configure(size=-px_size)
            while (
                self._measure_digit_font.measure(sample) > avail_w
                or self._measure_digit_font.metrics("linespace") > avail_h
            ) and px_size > 12:
                px_size -= 1
                self._measure_digit_font.configure(size=-px_size)

        sub_px = 11
        if self._show_status:
            sub_px = max(9, min(14, int(status_band_h * 0.55)))
            max_sub_w = max(40, w - 32)
            self._measure_status_font.configure(size=-sub_px)
            while self._measure_status_font.measure(self._status_text) > max_sub_w and sub_px > 8:
                sub_px -= 1
                self._measure_status_font.configure(size=-sub_px)

        self._cached_layout_key = layout_key
        self._cached_sizes = (px_size, sub_px, status_band_h)
        return self._cached_sizes

    def _redraw(self):
        """Полная перерисовка табло на Canvas."""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 40 or h < 20:
            return

        px_size, sub_px, status_band_h = self._compute_layout(w, h)
        if px_size != self._cur_digit_px:
            self._digit_font.configure(size=-px_size)
            self._cur_digit_px = px_size

        self.canvas.configure(bg=self._bg_color)
        self.canvas.delete("all")

        main_cx = w // 2
        main_cy = (h - status_band_h) // 2 if self._show_status else h // 2

        if self._transparent_mode:
            # Обводка основного табло для контрастности на любом фоне
            for ox, oy in OUTLINE_OFFSETS_MAIN:
                self.canvas.create_text(
                    main_cx + ox,
                    main_cy + oy,
                    text=self._time_text,
                    font=self._digit_font,
                    fill=self._outline_color,
                    anchor="center",
                    tags=("main_outline",),
                )

        # Основные цифры
        self.canvas.create_text(
            main_cx,
            main_cy,
            text=self._time_text,
            font=self._digit_font,
            fill=self._digit_color,
            anchor="center",
            tags=("main_fg",),
        )

        if self._show_status:
            if sub_px != self._cur_status_px:
                self._status_font.configure(size=-sub_px)
                self._cur_status_px = sub_px
            grip_px = max(9, min(12, status_band_h // 2))
            if grip_px != self._cur_grip_px:
                self._grip_font.configure(size=-grip_px)
                self._cur_grip_px = grip_px

            status_cx = w // 2
            status_cy = h - status_band_h // 2 - 2

            if self._transparent_mode:
                status_fill = "#2b2d3c" if _is_light_hex(self._outline_color) else "#d0d4e6"
                for ox, oy in OUTLINE_OFFSETS_STATUS:
                    self.canvas.create_text(
                        status_cx + ox,
                        status_cy + oy,
                        text=self._status_text,
                        font=self._status_font,
                        fill=self._outline_color,
                        anchor="center",
                        tags=("status_outline",),
                    )
            else:
                status_fill = "#5c5f77" if _is_light_hex(self._bg_color) else "#6c7086"

            # Статусная строка
            self.canvas.create_text(
                status_cx,
                status_cy,
                text=self._status_text,
                font=self._status_font,
                fill=status_fill,
                anchor="center",
                tags=("status_fg",),
            )

            # Визуальный уголок изменения размера
            grip_fill = "#7c8098" if self._transparent_mode else "#5c5f77"
            self.canvas.create_text(
                w - 4,
                h - 2,
                text="◢",
                font=self._grip_font,
                fill=grip_fill,
                anchor="se",
            )

    def _on_configure(self, event: tk.Event):
        if event.width < 40 or event.height < 20:
            return
        self._redraw()

    def set_digit_color(self, color: str):
        if color != self._digit_color:
            self._digit_color = color
            if self.canvas.find_withtag("main_fg"):
                self.canvas.itemconfigure("main_fg", fill=color)
            else:
                self._redraw()

    def update_time_text(self, text: str, fg: Optional[str] = None):
        old_pattern = re.sub(r"\d", "8", self._time_text)
        new_pattern = re.sub(r"\d", "8", text)
        changed = text != self._time_text or (fg is not None and fg != self._digit_color)
        self._time_text = text
        if fg:
            self._digit_color = fg
        if not changed:
            return
        if old_pattern == new_pattern and self.canvas.find_withtag("main_fg"):
            if self._transparent_mode:
                self.canvas.itemconfigure("main_outline", text=self._time_text)
            self.canvas.itemconfigure("main_fg", text=self._time_text, fill=self._digit_color)
        else:
            self._redraw()

    def set_status_text(self, text: str):
        if text != self._status_text:
            self._status_text = text
            if self._show_status:
                self._redraw()

    def set_show_status(self, show: bool):
        show = bool(show)
        if show != self._show_status:
            self._show_status = show
            self._redraw()

    def update_colors(
        self,
        bg: str,
        fg: str,
        transparent_mode: bool = False,
        outline_color: str = "#181825",
    ):
        self._bg_color = bg
        self._fg_color = fg
        self._digit_color = fg
        self._transparent_mode = transparent_mode
        self._outline_color = outline_color
        self.config(bg=bg)
        self.canvas.config(bg=bg)
        self._redraw()

    def bind_mouse_events(self):
        self.canvas.bind("<Motion>", self._on_mouse_hover)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-2>", lambda e: self.on_reset())
        self.canvas.bind("<ButtonRelease-3>", self._on_right_click)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", lambda e: self.on_wheel(60))
        self.canvas.bind("<Button-5>", lambda e: self.on_wheel(-60))

    def _determine_zone(self, event: tk.Event) -> str:
        """Определяет зону курсора: 4 угла, 4 края или перемещение."""
        win_w = self.parent.winfo_width()
        win_h = self.parent.winfo_height()
        x = event.x_root - self.parent.winfo_x()
        y = event.y_root - self.parent.winfo_y()

        corner_margin = 14
        edge_margin = 7

        if x <= corner_margin and y <= corner_margin:
            return "NW"
        if win_w - x <= corner_margin and y <= corner_margin:
            return "NE"
        if x <= corner_margin and win_h - y <= corner_margin:
            return "SW"
        if win_w - x <= corner_margin and win_h - y <= corner_margin:
            return "SE"

        if y <= edge_margin:
            return "N"
        if win_h - y <= edge_margin:
            return "S"
        if x <= edge_margin:
            return "W"
        if win_w - x <= edge_margin:
            return "E"
        return "MOVE"

    def _cursor_for_zone(self, zone: str) -> str:
        if sys.platform == "win32":
            mapping = {
                "NW": "size_nw_se",
                "SE": "size_nw_se",
                "NE": "size_ne_sw",
                "SW": "size_ne_sw",
                "W": "size_we",
                "E": "size_we",
                "N": "size_ns",
                "S": "size_ns",
                "MOVE": "fleur",
            }
        else:
            mapping = {
                "NW": "top_left_corner",
                "SE": "bottom_right_corner",
                "NE": "top_right_corner",
                "SW": "bottom_left_corner",
                "W": "sb_h_double_arrow",
                "E": "sb_h_double_arrow",
                "N": "sb_v_double_arrow",
                "S": "sb_v_double_arrow",
                "MOVE": "fleur",
            }
        return mapping.get(zone, "fleur")

    def _on_mouse_hover(self, event: tk.Event):
        """Динамическая смена курсора мыши при наведении на края и углы."""
        cursor = self._cursor_for_zone(self._determine_zone(event))
        if cursor != self._current_cursor:
            self._current_cursor = cursor
            try:
                self.canvas.config(cursor=cursor)
            except tk.TclError:
                pass

    def _on_right_click(self, event: tk.Event):
        self.on_context_menu(event)
        return "break"

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
        self._double_click_flag = False

    def _on_motion(self, event: tk.Event):
        dx = event.x_root - self.start_mouse_x
        dy = event.y_root - self.start_mouse_y

        if abs(dx) > 3 or abs(dy) > 3 or self.action_performed:
            self.action_performed = True

            if self.active_zone == "MOVE":
                nx = self.start_win_x + dx
                ny = self.start_win_y + dy
                self.parent.geometry(f"+{nx}+{ny}")
            else:
                new_x = self.start_win_x
                new_y = self.start_win_y
                new_w = self.start_win_w
                new_h = self.start_win_h

                if "E" in self.active_zone:
                    new_w = max(self.MIN_WIDTH, self.start_win_w + dx)
                if "W" in self.active_zone:
                    new_w = max(self.MIN_WIDTH, self.start_win_w - dx)
                    new_x = self.start_win_x + (self.start_win_w - new_w)
                if "S" in self.active_zone:
                    new_h = max(self.MIN_HEIGHT, self.start_win_h + dy)
                if "N" in self.active_zone:
                    new_h = max(self.MIN_HEIGHT, self.start_win_h - dy)
                    new_y = self.start_win_y + (self.start_win_h - new_h)

                self.parent.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")

    def _fire_single_click(self):
        self._click_job = None
        if not self._double_click_flag:
            self.on_click()

    def _on_release(self, event: tk.Event):
        if self.action_performed:
            if self.active_zone == "MOVE":
                self.on_drag_end()
            else:
                self.on_resize_end()
        elif self._double_click_flag:
            self._double_click_flag = False
        else:
            if self._click_job is not None:
                try:
                    self.after_cancel(self._click_job)
                except Exception:
                    pass
            self._click_job = self.after(200, self._fire_single_click)

    def _on_double_click(self, event: tk.Event):
        self._double_click_flag = True
        if self._click_job is not None:
            try:
                self.after_cancel(self._click_job)
            except Exception:
                pass
            self._click_job = None
        self.on_double_click()

    def _on_wheel(self, event: tk.Event):
        delta = 60 if event.delta > 0 else -60
        self.on_wheel(delta)
