from pydantic import BaseModel, Field
from typing import Optional

class AppConfig(BaseModel):
    """Статические системные настройки"""
    sample_rate: int = Field(default=44100, description="Частота дискретизации (Гц)")
    canvas_width: int = Field(default=700, description="Ширина холста в пикселях")
    canvas_height: int = Field(default=300, description="Высота холста в пикселях")

class GenerationParams(BaseModel):
    """
    Динамические параметры генерации мелодии. 
    """
    duration: float = Field(default=3.0, ge=1.0, le=10.0, description="Длительность мелодии (сек)")
    steps: int = Field(default=16, ge=4, le=64, description="Количество нот (темп звучания)")
    waveform: str = Field(default="sine", description="Тип волны: sine, square, sawtooth")
    template_name: Optional[str] = Field(default=None, description="Имя выбранного шаблона")