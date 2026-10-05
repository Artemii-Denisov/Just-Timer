"""
Удобная точка запуска приложения из корня проекта.
Запуск: py run.py
"""

import sys
import os

# Добавляем каталог src в sys.path
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from timer_app.__main__ import main
from timer_app.app import TimerApplication

if __name__ == "__main__":
    main()
