"""
Модуль глобальных горячих клавиш Windows (Win32 RegisterHotKey).
Позволяет управлять таймером из любого приложения без переключения окна.
"""

import sys
import threading
from typing import Callable

try:
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
except Exception:
    user32 = None


class GlobalHotkeysManager:
    """
    Фоновый слушатель глобальных сочетаний клавиш:
      Ctrl + Alt + Space -> Старт / Пауза
      Ctrl + Alt + R     -> Сброс
    """
    def __init__(self, on_toggle: Callable[[], None], on_reset: Callable[[], None]):
        self.on_toggle = on_toggle
        self.on_reset = on_reset
        self.thread: threading.Thread = None
        self.thread_id: int = 0
        self.running: bool = False

    def start(self) -> bool:
        if not user32 or self.running:
            return False

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        if not self.running:
            return
        self.running = False
        if user32 and self.thread_id:
            try:
                # Отправляем WM_QUIT потоку для выхода из GetMessageW
                user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)
            except Exception:
                pass

    def _loop(self):
        self.thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

        # Модификаторы: MOD_CONTROL (0x2) | MOD_ALT (0x1) | MOD_NOREPEAT (0x4000)
        MODS = 0x0002 | 0x0001 | 0x4000
        VK_SPACE = 0x20
        VK_R = 0x52

        HOTKEY_TOGGLE_ID = 101
        HOTKEY_RESET_ID = 102

        success_toggle = user32.RegisterHotKey(None, HOTKEY_TOGGLE_ID, MODS, VK_SPACE)
        success_reset = user32.RegisterHotKey(None, HOTKEY_RESET_ID, MODS, VK_R)

        if not success_toggle or not success_reset:
            print("[Hotkeys] Предупреждение: некоторые глобальные клавиши уже заняты другой программой.")

        msg = wintypes.MSG()
        while self.running:
            res = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if res <= 0:
                break

            if msg.message == 0x0312:  # WM_HOTKEY
                if msg.wParam == HOTKEY_TOGGLE_ID:
                    try:
                        self.on_toggle()
                    except Exception as e:
                        print(f"[Hotkeys] Ошибка вызова on_toggle: {e}")
                elif msg.wParam == HOTKEY_RESET_ID:
                    try:
                        self.on_reset()
                    except Exception as e:
                        print(f"[Hotkeys] Ошибка вызова on_reset: {e}")

            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        user32.UnregisterHotKey(None, HOTKEY_TOGGLE_ID)
        user32.UnregisterHotKey(None, HOTKEY_RESET_ID)
