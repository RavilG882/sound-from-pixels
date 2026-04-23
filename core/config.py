from pydantic import BaseModel

class AppConfig(BaseModel):
    """Параметры звука и холста"""
    sample_rate: int = 44100
    duration: float = 3.0
    min_freq: float = 200.0
    max_freq: float = 1000.0
    canvas_width: int = 700
    canvas_height: int = 300
