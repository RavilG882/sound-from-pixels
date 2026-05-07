import numpy as np
from scipy.interpolate import interp1d
from typing import Tuple

from .config import AppConfig
from .exceptions import EmptyCanvasError

class AudioSynthesizer:
    """Санитайзер"""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    @property
    def config(self) -> AppConfig:
        return self._config

    @staticmethod
    def extract_coordinates(image_rgba: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if image_rgba is None or image_rgba.size == 0:
            raise EmptyCanvasError("Изображение не найдено.")
        drawn_pixels = image_rgba[:, :, 0] > 0
        y_coords, x_coords = np.nonzero(drawn_pixels)
        if len(x_coords) == 0:
            raise EmptyCanvasError("Холст пуст. Нарисуйте кривую.")
        unique_x, indices = np.unique(x_coords, return_inverse=True)
        unique_y = np.zeros_like(unique_x, dtype=np.float64)
        np.add.at(unique_y, indices, y_coords)
        unique_y /= np.bincount(indices)

        return unique_x, unique_y
    def generate_melody(self, image_rgba: np.ndarray) -> Tuple[np.ndarray, list]:
        x, y = self.extract_coordinates(image_rgba)

        if len(x) < 2:
            raise EmptyCanvasError("Слишком короткая линия.")

        f_interp = interp1d(x, y, kind='linear', bounds_error=False, fill_value=(y[0], y[-1]))
        steps = 16 
        samples_per_step = int((self.config.sample_rate * self.config.duration) / steps)

        step_x = np.linspace(0, self.config.canvas_width, steps)
        step_y = f_interp(step_x)
        scale = np.array([
            130.81, 146.83, 164.81, 174.61, 196.00, 220.00, 246.94, # Низкие
            261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, # Средние
            523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77, # Высокие
            1046.50 # Пик
        ])
        
        # Переворачиваем холст и находим индексы нот
        normalized_y = 1.0 - (step_y / self.config.canvas_height)
        normalized_y = np.clip(normalized_y, 0.0, 1.0)
        
        indices = np.round(normalized_y * (len(scale) - 1)).astype(int)
        step_freqs = scale[indices]

        audio = []
        dt = 1.0 / self.config.sample_rate

        for freq in step_freqs:
            t = np.arange(samples_per_step) * dt
            
            # Пианино
            note = (
                1.00 * np.sin(2 * np.pi * freq * t) +
                0.50 * np.sin(2 * np.pi * (freq * 2) * t) +
                0.25 * np.sin(2 * np.pi * (freq * 3) * t) +
                0.12 * np.sin(2 * np.pi * (freq * 4) * t)
            )

            #Четкий звук и затухание
            envelope = np.exp(-6.0 * t / (samples_per_step * dt)) 
            envelope[:200] *= np.linspace(0, 1, 200)   # Плавный старт (без щелчка)
            envelope[-200:] *= np.linspace(1, 0, 200)  # Плавный конец

            audio.append(note * envelope)

        # Склеиваем и выравниваем громкость
        final_audio = np.concatenate(audio)
        final_audio = final_audio / np.max(np.abs(final_audio))

        # Формируем список сыгранных частот для вывода
        played_notes = [f"{int(f)} Гц" for f in step_freqs]

        return final_audio, played_notes