import numpy as np
from core.config import AppConfig, GenerationParams
from core.synthesizer import AudioSynthesizer

def test_synthesis_without_ui():
    config = AppConfig()
    params = GenerationParams(duration=2.0, steps=8, waveform="square")
    synth = AudioSynthesizer(config)
    
    test_template = [7, 8, 9, 10]
    audio, notes = synth.generate_from_template(test_template, params)
    
    assert len(audio) > 0, "Массив аудио пуст"
    assert len(notes) == 8, "Количество нот не совпадает с params.steps"
    print("Тест пройден успешно!")

if __name__ == "__main__":
    test_synthesis_without_ui()