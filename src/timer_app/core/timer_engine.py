"""
Ядро логики таймера (независимое от GUI).
Обеспечивает точный отсчет через time.monotonic().
"""

import time
from typing import Tuple


class TimerEngine:
    def __init__(self, initial_duration: float = 900.0):
        self.initial_duration: float = max(0.1, float(initial_duration))
        self.remaining: float = self.initial_duration
        self.is_running: bool = False
        self.is_finished: bool = False
        self.target_time: float = 0.0

    def start(self) -> None:
        """Запуск или возобновление отсчета."""
        if self.is_finished or self.remaining <= 0:
            self.reset()
        self.is_running = True
        self.is_finished = False
        self.target_time = time.monotonic() + self.remaining

    def pause(self) -> None:
        """Приостановка отсчета."""
        if self.is_running:
            now = time.monotonic()
            self.remaining = max(0.0, self.target_time - now)
            self.is_running = False

    def toggle(self) -> bool:
        """
        Переключение между Старт и Пауза.
        Возвращает True если запущен, False если на паузе.
        """
        if self.is_running:
            self.pause()
            return False
        else:
            self.start()
            return True

    def reset(self) -> None:
        """Сброс к исходному значению длительности."""
        self.is_running = False
        self.is_finished = False
        self.remaining = self.initial_duration

    def set_duration(self, seconds: float) -> None:
        """Установка новой длительности."""
        was_running = self.is_running
        self.is_running = False
        self.is_finished = False
        self.initial_duration = max(1.0, float(seconds))
        self.remaining = self.initial_duration
        if was_running:
            self.start()

    def adjust_duration(self, delta_seconds: float) -> None:
        """Быстрая подстройка времени (+ / - N секунд)."""
        new_time = max(1.0, self.initial_duration + delta_seconds)
        self.set_duration(new_time)

    def tick(self) -> Tuple[float, bool]:
        """
        Очередной тик таймера.
        Возвращает кортеж (оставшиеся_секунды, завершился_ли_прямо_сейчас).
        """
        if not self.is_running:
            return self.remaining, False

        now = time.monotonic()
        remaining = self.target_time - now

        if remaining <= 0.05:
            self.remaining = 0.0
            self.is_running = False
            self.is_finished = True
            return 0.0, True

        self.remaining = remaining
        return remaining, False
