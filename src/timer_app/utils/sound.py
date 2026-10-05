"""
Модуль воспроизведения и настройки звуков окончания таймера.
Поддерживает системные звуки Windows (.wav), мелодичный сигнал Beep и пользовательские файлы.
"""

import os
import time
import threading
from typing import Dict, Optional

try:
    import winsound
except ImportError:
    winsound = None

# Встроенные пресеты звуков Windows
SOUND_PRESETS: Dict[str, str] = {
    "Дзынь (Ding)": r"C:\Windows\Media\ding.wav",
    "Короткий сигнал (Beep)": "SHORT_BEEP",
    "Колокольчики (Chimes)": r"C:\Windows\Media\chimes.wav",
    "Уведомление (Notify)": r"C:\Windows\Media\notify.wav",
    "Та-да! (Tada)": r"C:\Windows\Media\tada.wav",
    "Будильник (Alarm)": r"C:\Windows\Media\Alarm01.wav",
    "Мелодичный перезвон (Beep)": "BEEP",
}


def _play_short_beep():
    """Синтезирует четкий одиночный сигнал окончания круга."""
    if not winsound:
        return
    try:
        winsound.Beep(1046, 180)  # C6, 180ms
    except Exception:
        pass


def _play_melodic_beep():
    """Синтезирует приятный мелодичный перезвон из трех нот."""
    if not winsound:
        return
    try:
        # Ноты D5, A5, D6 (арпеджио)
        for freq, duration in [(587, 120), (880, 120), (1174, 250)]:
            winsound.Beep(freq, duration)
            time.sleep(0.04)
    except Exception:
        pass


def play_sound_by_type(sound_type: str, custom_path: Optional[str] = None):
    """
    Воспроизводит выбранный звук асинхронно в фоновом потоке.
    """
    if not winsound:
        return

    def _play():
        try:
            if sound_type == "Пользовательский" and custom_path and os.path.exists(custom_path):
                winsound.PlaySound(custom_path, winsound.SND_FILENAME)
                return

            if sound_type == "Короткий сигнал (Beep)":
                _play_short_beep()
                return

            if sound_type == "Мелодичный перезвон (Beep)":
                _play_melodic_beep()
                return

            wav_path = SOUND_PRESETS.get(sound_type, SOUND_PRESETS["Дзынь (Ding)"])
            if os.path.exists(wav_path):
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
            else:
                # Резервный системный колокольчик
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        except Exception as e:
            print(f"[Sound] Ошибка воспроизведения: {e}")

    threading.Thread(target=_play, daemon=True).start()


def play_finish_sound(sound_type: str = "Дзынь (Ding)", custom_path: Optional[str] = None):
    """Воспроизведение звука при окончании таймера (все круги завершены)."""
    play_sound_by_type(sound_type, custom_path)


def play_round_sound(sound_type: str = "Короткий сигнал (Beep)", custom_path: Optional[str] = None):
    """Воспроизведение звука при завершении промежуточного круга/раунда."""
    play_sound_by_type(sound_type, custom_path)


def preview_sound(sound_type: str, custom_path: Optional[str] = None):
    """Предпрослушивание звука из меню настроек."""
    play_sound_by_type(sound_type, custom_path)
