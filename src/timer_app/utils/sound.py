"""
Модуль воспроизведения и настройки звуков окончания таймера.
Поддерживает системные звуки Windows (.wav), системные аудиоплееры Linux/macOS
и встроенный синтезатор WAV-тонов на базе стандартной библиотеки.
"""

import math
import os
import shutil
import struct
import subprocess
import tempfile
import threading
import time
import wave
from typing import Dict, List, Optional, Sequence, Tuple

try:
    import winsound
except ImportError:
    winsound = None

# Встроенные пресеты звуков Windows / кроссплатформенные пресеты
SOUND_PRESETS: Dict[str, str] = {
    "Дзынь (Ding)": r"C:\Windows\Media\ding.wav",
    "Короткий сигнал (Beep)": "SHORT_BEEP",
    "Колокольчики (Chimes)": r"C:\Windows\Media\chimes.wav",
    "Уведомление (Notify)": r"C:\Windows\Media\notify.wav",
    "Та-да! (Tada)": r"C:\Windows\Media\tada.wav",
    "Будильник (Alarm)": r"C:\Windows\Media\Alarm01.wav",
    "Мелодичный перезвон (Beep)": "BEEP",
}

# Нотные последовательности (частота Гц, длительность сек) для синтеза WAV-файлов
SYNTH_PRESET_NOTES: Dict[str, Tuple[str, List[Tuple[float, float]]]] = {
    "Дзынь (Ding)": ("ding.wav", [(1046.5, 0.45)]),
    "Короткий сигнал (Beep)": ("short_beep.wav", [(1046.5, 0.18)]),
    "Колокольчики (Chimes)": ("chimes.wav", [(1046.5, 0.18), (1318.5, 0.18), (1567.98, 0.32)]),
    "Уведомление (Notify)": ("notify.wav", [(783.99, 0.14), (1046.5, 0.22)]),
    "Та-да! (Tada)": ("tada.wav", [(523.25, 0.12), (659.25, 0.12), (783.99, 0.12), (1046.5, 0.40)]),
    "Будильник (Alarm)": ("alarm.wav", [(880.0, 0.15), (0.0, 0.08), (880.0, 0.15), (0.0, 0.08), (880.0, 0.25)]),
    "Мелодичный перезвон (Beep)": ("melodic_beep.wav", [(587.33, 0.14), (880.0, 0.14), (1174.66, 0.30)]),
}


def _generate_wav_tone(notes: Sequence[Tuple[float, float]], filename: str) -> Optional[str]:
    """
    Синтезирует чистый .wav файл с экспоненциальным затуханием во временный каталог.
    Возвращает путь к файлу или None в случае ошибки.
    """
    try:
        out_path = os.path.join(tempfile.gettempdir(), f"just_timer_{filename}")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 44:
            return out_path

        sample_rate = 22050
        samples: List[int] = []
        attack_samples = int(0.005 * sample_rate)

        for freq, duration_sec in notes:
            num_samples = max(1, int(sample_rate * duration_sec))
            if freq <= 0:
                samples.extend([0] * num_samples)
                continue

            for i in range(num_samples):
                t = i / sample_rate
                attack = min(1.0, i / max(1, attack_samples))
                decay = math.exp(-4.5 * t / max(0.01, duration_sec))
                val = int(32767 * 0.45 * attack * decay * math.sin(2.0 * math.pi * freq * t))
                samples.append(max(-32768, min(32767, val)))

        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

        return out_path
    except Exception as e:
        print(f"[Sound] Ошибка синтеза WAV: {e}")
        return None


def _get_preset_wav(sound_type: str) -> Optional[str]:
    """Возвращает путь к синтезированному WAV для указанного пресета."""
    entry = SYNTH_PRESET_NOTES.get(sound_type, SYNTH_PRESET_NOTES["Дзынь (Ding)"])
    filename, notes = entry
    return _generate_wav_tone(notes, filename)


def _play_short_beep():
    """Синтезирует четкий одиночный сигнал окончания круга (Windows)."""
    if not winsound:
        return
    try:
        winsound.Beep(1046, 180)
    except Exception:
        pass


def _play_melodic_beep():
    """Синтезирует приятный мелодичный перезвон из трех нот (Windows)."""
    if not winsound:
        return
    try:
        for freq, duration in [(587, 120), (880, 120), (1174, 250)]:
            winsound.Beep(freq, duration)
            time.sleep(0.04)
    except Exception:
        pass


def _play_unix_wav(wav_path: str):
    """Воспроизводит WAV-файл на Linux/macOS через доступный системный плеер."""
    candidates = [
        ["paplay", wav_path],
        ["pw-play", wav_path],
        ["aplay", "-q", wav_path],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", wav_path],
        ["afplay", wav_path],
    ]
    for cmd in candidates:
        if shutil.which(cmd[0]):
            try:
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except Exception:
                continue


def play_sound_by_type(sound_type: str, custom_path: Optional[str] = None):
    """
    Воспроизводит выбранный звук асинхронно в фоновом потоке.
    """
    def _play():
        try:
            if winsound:
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
                if wav_path and os.path.exists(wav_path):
                    winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                    return

                synth_path = _get_preset_wav(sound_type)
                if synth_path and os.path.exists(synth_path):
                    winsound.PlaySound(synth_path, winsound.SND_FILENAME)
                else:
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            else:
                # Linux / macOS
                if sound_type == "Пользовательский" and custom_path and os.path.exists(custom_path):
                    _play_unix_wav(custom_path)
                    return
                synth_path = _get_preset_wav(sound_type)
                if synth_path and os.path.exists(synth_path):
                    _play_unix_wav(synth_path)
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
