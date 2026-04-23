import streamlit as st
import scipy.io.wavfile as wavf
import numpy as np
import io
from streamlit_drawable_canvas import st_canvas

from core.config import AppConfig
from core.synthesizer import AudioSynthesizer
from core.exceptions import SonificationError

def main() -> None:
    st.set_page_config(page_title="Data Sonification", layout="centered")
    st.title("🎹 Звук из пикселей")
    st.markdown("Нарисуй кривую. Программа разобьет её на 16 нот и сыграет мелодию.")

    config = AppConfig()
    
    canvas_result = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=4,
        stroke_color="#FFFFFF",
        background_color="#000000",
        height=config.canvas_height,
        width=config.canvas_width,
        drawing_mode="freedraw",
        key="canvas",
    )

    if st.button("Сгенерировать мелодию"):
        if canvas_result.image_data is not None:
            try:
                synth = AudioSynthesizer(config)
                
                # аудио, список частот
                audio_array, played_notes = synth.generate_melody(canvas_result.image_data)
                
                audio_int16 = np.int16(audio_array * 32767)
                wav_io = io.BytesIO()
                wavf.write(wav_io, config.sample_rate, audio_int16)
                
                # Выводим плеер
                st.audio(wav_io, format="audio/wav")
                
                # Выводим сыгранные ноты(проверка, что меняются корректно)
                st.success("Успешно сгенерировано!")
                st.info(f"**Сыгранные частоты:** {', '.join(played_notes)}")
                
            except SonificationError as e:
                st.warning(f"Ошибка: {e}")
            except Exception as e:
                st.error(f"Непредвиденная ошибка: {e}")
        else:
            st.warning("Нарисуйте линию перед генерацией.")

if __name__ == "__main__":
    main()