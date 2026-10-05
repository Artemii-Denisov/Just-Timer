"""
Звуковые оповещения для Windows.
"""

import time
import threading

try:
    import winsound
except ImportError:
    winsound = None


def play_finish_sound():
    """
    Воспроизводит мягкий тройной сигнал в отдельном потоке,
    чтобы не блокировать графический интерфейс.
    """
    if not winsound:
        return

    def _beep():
        try:
            for _ in range(3):
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                time.sleep(0.3)
        except Exception:
            pass

    threading.Thread(target=_beep, daemon=True).start()
