import sys
import os

try:
    import ctypes
    app_id = "Denis.JustTimer.App.1.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
except Exception:
    pass

# Добавляем каталог src в sys.path
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from timer_app.__main__ import main
from timer_app.app import TimerApplication

if __name__ == "__main__":
    main()
