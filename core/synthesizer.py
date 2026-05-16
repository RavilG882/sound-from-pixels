import numpy as np
from scipy.interpolate import interp1d
from scipy import signal
from typing import Tuple, List

from .config import AppConfig, GenerationParams
from .exceptions import EmptyCanvasError

class AudioSynthesizer:
    """
    Ядро цифровой обработки сигналов (DSP).
    Отвечает за парсинг координат, квантование и генерацию PCM-массивов.
    """

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    @property
    def config(self) -> AppConfig:
        return self._config

    def _get_scale(self) -> np.ndarray:
        """Возвращает массив частот"""
        return np.array([
            130.81, 146.83, 164.81, 174.61, 196.00, 220.00, 246.94,
            261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88,
            523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77,
            1046.50
        ])

    @staticmethod
    def extract_coordinates(image_rgba: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Извлекает усредненные координаты линии из матрицы изображения.

        Args:
            image_rgba (np.ndarray): RGBA матрица холста.

        Returns:
            Tuple[np.ndarray, np.ndarray]: Массивы X и Y координат.
            
        Raises:
            EmptyCanvasError: При пустом входном массиве или отсутствии нарисованных линий.
        """
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

    def _generate_oscillator(self, freq: float, t: np.ndarray, waveform: str) -> np.ndarray:
        """Генерирует звуковую волну выбранного типа"""
        phase = 2 * np.pi * freq * t
        if waveform == "square":
            return 0.8 * signal.square(phase)
        elif waveform == "sawtooth":
            return 0.8 * signal.sawtooth(phase)
        else:
            return (
                1.00 * np.sin(phase) +
                0.50 * np.sin(phase * 2) +
                0.25 * np.sin(phase * 3)
            )

    def _synthesize_audio(self, indices: np.ndarray, params: GenerationParams) -> Tuple[np.ndarray, List[str]]:
        """
        Универсальный метод генерации аудио из индексов нот.
        Принимает параметры напрямую из Pydantic-модели для изоляции от Streamlit.
        """
        scale = self._get_scale()
        step_freqs = scale[indices]
        
        samples_per_step = int((self.config.sample_rate * params.duration) / params.steps)
        audio = []
        dt = 1.0 / self.config.sample_rate

        for freq in step_freqs:
            t = np.arange(samples_per_step) * dt
            
            note = self._generate_oscillator(freq, t, params.waveform)

            # Алгоритмическое сглаживание: амплитудная огибающая (Envelope)
            envelope = np.exp(-6.0 * t / (samples_per_step * dt)) 
            envelope[:200] *= np.linspace(0, 1, 200)
            envelope[-200:] *= np.linspace(1, 0, 200)

            audio.append(note * envelope)

        final_audio = np.concatenate(audio)
        final_audio = final_audio / np.max(np.abs(final_audio))
        played_notes = [f"{int(f)} Гц" for f in step_freqs]

        return final_audio, played_notes

    def generate_melody(self, image_rgba: np.ndarray, params: GenerationParams) -> Tuple[np.ndarray, List[str]]:
        """Генерация аудио из пользовательского рисунка."""
        x, y = self.extract_coordinates(image_rgba)

        if len(x) < 2:
            raise EmptyCanvasError("Слишком короткая линия.")

        f_interp = interp1d(x, y, kind='linear', bounds_error=False, fill_value=(y[0], y[-1]))
        step_x = np.linspace(0, self.config.canvas_width, params.steps)
        step_y = f_interp(step_x)

        normalized_y = 1.0 - (step_y / self.config.canvas_height)
        normalized_y = np.clip(normalized_y, 0.0, 1.0)
        
        scale = self._get_scale()
        indices = np.round(normalized_y * (len(scale) - 1)).astype(int)

        return self._synthesize_audio(indices, params)

    def generate_from_template(self, indices_list: List[int], params: GenerationParams) -> Tuple[np.ndarray, List[str]]:
        """Генерация аудио из заранее заданного массива шаблона."""
        # Подгоняем длину шаблона под выбранное число нот(темп)
        indices = np.array(indices_list)
        f_interp = interp1d(np.linspace(0, 1, len(indices)), indices, kind='nearest')
        stretched_indices = f_interp(np.linspace(0, 1, params.steps)).astype(int)
        
        return self._synthesize_audio(stretched_indices, params)