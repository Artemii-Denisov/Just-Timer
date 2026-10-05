"""
Точка входа при запуске через `python -m timer_app`.
"""

import sys
import tkinter as tk
from .app import TimerApplication


def main():
    root = tk.Tk()
    app = TimerApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()
