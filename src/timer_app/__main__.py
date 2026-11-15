"""
Точка входа при запуске через `python -m timer_app`.
"""

import sys
import tkinter as tk
from .app import TimerApplication, APP_USER_MODEL_ID


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
        except Exception:
            pass
    root = tk.Tk()
    app = TimerApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()
