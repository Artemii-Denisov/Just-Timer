"""
Ядро логики таймера (независимое от GUI).
Обеспечивает точный отсчет через time.monotonic().
Поддерживает обычный таймер, круги/раунды (например, 5 кругов по 30 сек) и интервалы.
"""

import time
from typing import Tuple, Optional


class TimerEngine:
    def __init__(
        self,
        initial_duration: float = 900.0,
        total_rounds: int = 1,
        rest_duration: float = 0.0
    ):
        self.work_duration: float = max(0.1, float(initial_duration))
        self.initial_duration: float = self.work_duration  # Для обратной совместимости
        self.total_rounds: int = max(0, int(total_rounds))  # 0 = бесконечный цикл, 1 = обычный, >1 = раунды
        self.rest_duration: float = max(0.0, float(rest_duration))

        self.current_round: int = 1
        self.is_rest: bool = False
        self.remaining: float = self.work_duration
        self.is_running: bool = False
        self.is_finished: bool = False
        self.target_time: float = 0.0
        self.last_event: Optional[str] = None

    def start(self) -> None:
        """Запуск или возобновление отсчета."""
        if self.is_finished or self.remaining <= 0:
            self.reset()
        self.is_running = True
        self.is_finished = False
        self.last_event = None
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
        """Полный сброс к началу (1-й круг)."""
        self.is_running = False
        self.is_finished = False
        self.current_round = 1
        self.is_rest = False
        self.remaining = self.work_duration
        self.last_event = None

    def set_duration(self, seconds: float) -> None:
        """Установка длительности рабочего раунда."""
        was_running = self.is_running
        self.is_running = False
        self.is_finished = False
        self.work_duration = max(1.0, float(seconds))
        self.initial_duration = self.work_duration
        self.reset()
        if was_running:
            self.start()

    def set_rounds_mode(
        self,
        total_rounds: int,
        work_duration: float,
        rest_duration: float = 0.0
    ) -> None:
        """Настройка кругового/интервального режима."""
        was_running = self.is_running
        self.is_running = False
        self.is_finished = False
        self.total_rounds = max(0, int(total_rounds))
        self.work_duration = max(1.0, float(work_duration))
        self.initial_duration = self.work_duration
        self.rest_duration = max(0.0, float(rest_duration))
        self.reset()
        if was_running:
            self.start()

    def adjust_duration(self, delta_seconds: float) -> None:
        """Быстрая подстройка времени (+ / - N секунд)."""
        new_time = max(1.0, self.work_duration + delta_seconds)
        self.set_duration(new_time)

    def tick(self) -> Tuple[float, bool]:
        """
        Очередной тик таймера.
        Возвращает (оставшиеся_секунды, произошло_ли_событие).
        Тип события сохраняется в self.last_event:
          - 'round_rest': завершился раунд, начался отдых
          - 'round_next': завершился раунд (или отдых), начался следующий круг
          - 'all_finished': завершены все круги
        """
        if not self.is_running:
            return self.remaining, False

        now = time.monotonic()
        remaining = self.target_time - now

        if remaining <= 0.05:
            # 1. Если был раунд работы и настроен отдых -> переход к отдыху
            if self.rest_duration > 0 and not self.is_rest:
                self.is_rest = True
                self.remaining = self.rest_duration
                self.target_time = time.monotonic() + self.remaining
                self.last_event = "round_rest"
                return self.remaining, True

            # 2. Окончание раунда (или отдыха): проверяем, есть ли следующий круг
            self.is_rest = False
            if self.total_rounds == 0 or self.current_round < self.total_rounds:
                self.current_round += 1
                self.remaining = self.work_duration
                self.target_time = time.monotonic() + self.remaining
                self.last_event = "round_next"
                return self.remaining, True
            else:
                # 3. Все круги завершены!
                self.remaining = 0.0
                self.is_running = False
                self.is_finished = True
                self.last_event = "all_finished"
                return 0.0, True

        self.remaining = remaining
        return remaining, False
