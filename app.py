import streamlit as st
import scipy.io.wavfile as wavf
import numpy as np
import io
from streamlit_drawable_canvas import st_canvas

from core.config import AppConfig, GenerationParams
from core.synthesizer import AudioSynthesizer
from core.exceptions import SonificationError

# === ШАБЛОНЫ ===
TEMPLATES = {
    "Свой рисунок (Холст)": None,
    
    "Бетховен - Ода к радости": {
        "notes": [9, 9, 10, 11, 11, 10, 9, 8, 7, 7, 8, 9, 9, 8, 8, 8,
                  9, 9, 10, 11, 11, 10, 9, 8, 7, 7, 8, 9, 8, 7, 7, 7],
        "duration": 8.0,
        "steps": 32,
        "waveform": "sine"
    },
    
    "Tetris Theme": {
        "notes": [9, 6, 7, 8, 7, 6, 5, 5, 7, 9, 8, 7, 6, 6, 7, 8, 9, 7, 5, 5],
        "duration": 5.0,
        "steps": 20,          
        "waveform": "square"
    },
    
    "Mortal Kombat Theme (Драйв)": {
        "notes": [12, 12, 14, 12, 15, 15, 16, 15, 14, 14, 16, 14, 11, 11, 13, 11,
                  12, 12, 14, 12, 15, 15, 16, 15, 14, 14, 16, 14, 11, 11, 13, 11],
        "duration": 5.0,
        "steps": 32,
        "waveform": "sawtooth"
    }
}

def main() -> None:
    st.set_page_config(page_title="Data Sonification", layout="wide")
    st.title("🎹 Звук из пикселей")

    sys_config = AppConfig()
    
    # --- ОСНОВНАЯ ОБЛАСТЬ ---
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_template_name = st.selectbox("Источник мелодии:", list(TEMPLATES.keys()))

    # --- БОКОВАЯ ПАНЕЛЬ: НАСТРОЙКИ ---
    with st.sidebar:
        st.header("Настройки синтеза")
        
        # Если рисует пользователь, то может использовать ползунки
        if selected_template_name == "Свой рисунок (Холст)":
            duration = st.slider("Длительность (сек):", 1.0, 10.0, 3.0, 0.5)
            steps = st.slider("Число нот (Темп):", 4, 64, 16, 4)
            waveform = st.selectbox("Форма волны (Тембр):", ["sine", "square", "sawtooth"])
        
        # Если выбран шаблон — блокируем ручной ввод и ставим идеальные значения
        else:
            preset = TEMPLATES[selected_template_name]
            duration = preset["duration"]
            steps = preset["steps"]
            waveform = preset["waveform"]
            
            st.success("✨ Режим авто-настройки")
            st.info("Параметры заблокированы и подобраны автоматически для идеального звучания этой мелодии.")
            st.metric("Длительность", f"{duration} сек")
            st.metric("Количество шагов", f"{steps}")
            st.metric("Тембр", f"{waveform.capitalize()}")

        params = GenerationParams(
            duration=duration,
            steps=steps,
            waveform=waveform
        )

    # --- ОТРИСОВКА ГРАФИКА ИЛИ ХОЛСТА ---
    with col1:
        if selected_template_name == "Свой рисунок (Холст)":
            canvas_result = st_canvas(
                fill_color="rgba(0,0,0,0)",
                stroke_width=4,
                stroke_color="#FFFFFF",
                background_color="#000000",
                height=sys_config.canvas_height,
                width=sys_config.canvas_width,
                drawing_mode="freedraw",
                key="canvas",
            )
        else:
            st.markdown(f"**Графическая форма:** {selected_template_name}")
            st.line_chart(TEMPLATES[selected_template_name]["notes"], height=sys_config.canvas_height)

    # --- ГЕНЕРАЦИЯ ---
    with col2:
        st.markdown("### Генератор")
        if st.button("Сгенерировать мелодию", type="primary", use_container_width=True):
            try:
                synth = AudioSynthesizer(sys_config)
                
                if selected_template_name == "Свой рисунок (Холст)":
                    if canvas_result.image_data is None:
                        st.warning("Нарисуйте линию перед генерацией.")
                        return
                    audio_array, played_notes = synth.generate_melody(canvas_result.image_data, params)
                else:
                    # Передаем массив нот из нашего словаря
                    audio_array, played_notes = synth.generate_from_template(TEMPLATES[selected_template_name]["notes"], params)
                
                audio_int16 = np.int16(audio_array * 32767)
                wav_io = io.BytesIO()
                wavf.write(wav_io, sys_config.sample_rate, audio_int16)
                
                st.audio(wav_io, format="audio/wav")
                st.success("Успешно!")
                
                with st.expander("Посмотреть сыгранные частоты"):
                    st.write(", ".join(played_notes))
                
            except SonificationError as e:
                st.warning(f"Ошибка: {e}")
            except Exception as e:
                st.error(f"Непредвиденная ошибка: {e}")

if __name__ == "__main__":
    main()