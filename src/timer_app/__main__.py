"""
Точка входа при запуске через `python -m timer_app`.
"""

import sys
import tkinter as tk
from .app import TimerApplication


def main():
    try:
        import ctypes
        app_id = "Denis.JustTimer.App.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass
    root = tk.Tk()
    app = TimerApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()
