import gradio as gr
import torch
import os
from datetime import datetime

# === Cache settings (portable) ===
script_dir = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(script_dir, 'cache')
torch_cache = os.path.join(cache_dir, 'torch')
os.makedirs(torch_cache, exist_ok=True)
torch.hub.set_dir(torch_cache)

# Outputs folder
outputs_dir = os.path.join(script_dir, 'outputs')
os.makedirs(outputs_dir, exist_ok=True)

# === Device selection (GPU/CPU) ===
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"[INFO] Using device: {device}")
if device.type == 'cuda':
    print(f"[INFO] GPU: {torch.cuda.get_device_name(0)}")

# === Available models configuration ===
# Correct speakers based on models.yml from snakers4/silero-models
LANGUAGES = {
    'Russian': {
        'lang': 'ru',
        'model': 'v5_5_ru',
        'speakers': ['aidar', 'baya', 'kseniya', 'xenia', 'eugene', 'random'],
        'put_accent': True,
        'put_yo': True
    },
    'English': {
        'lang': 'en',
        'model': 'v3_en',
        'speakers': ['en_0', 'en_1', 'en_2', 'en_3', 'en_4', 'en_5', 'en_6', 'en_7', 'en_8', 'en_9',
                     'en_10', 'en_11', 'en_12', 'en_13', 'en_14', 'en_15', 'en_16', 'en_17', 'en_18', 'en_19',
                     'en_20', 'en_21', 'en_22', 'en_23', 'en_24', 'en_25', 'en_26', 'en_27', 'en_28', 'en_29',
                     'en_30', 'en_31', 'en_32', 'en_33', 'en_34', 'en_35', 'en_36', 'en_37', 'en_38', 'en_39',
                     'en_40', 'en_41', 'en_42', 'en_43', 'en_44', 'en_45', 'en_46', 'en_47', 'en_48', 'en_49',
                     'en_50', 'en_51', 'en_52', 'en_53', 'en_54', 'en_55', 'en_56', 'en_57', 'en_58', 'en_59',
                     'en_60', 'en_61', 'en_62', 'en_63', 'en_64', 'en_65', 'en_66', 'en_67', 'en_68', 'en_69',
                     'en_70', 'en_71', 'en_72', 'en_73', 'en_74', 'en_75', 'en_76', 'en_77', 'en_78', 'en_79',
                     'en_80', 'en_81', 'en_82', 'en_83', 'en_84', 'en_85', 'en_86', 'en_87', 'en_88', 'en_89',
                     'en_90', 'en_91', 'en_92', 'en_93', 'en_94', 'en_95', 'en_96', 'en_97', 'en_98', 'en_99',
                     'en_100', 'en_101', 'en_102', 'en_103', 'en_104', 'en_105', 'en_106', 'en_107', 'en_108',
                     'en_109', 'en_110', 'en_111', 'en_112', 'en_113', 'en_114', 'en_115', 'en_116', 'en_117'],
        'put_accent': False,
        'put_yo': False
    },
    'German': {
        'lang': 'de',
        'model': 'v3_de',
        'speakers': ['bernd_ungerer'],
        'put_accent': False,
        'put_yo': False
    },
    'Spanish': {
        'lang': 'es',
        'model': 'v3_es',
        'speakers': ['es_0', 'es_1', 'es_2'],
        'put_accent': False,
        'put_yo': False
    },
    'French': {
        'lang': 'fr',
        'model': 'v3_fr',
        'speakers': ['fr_0', 'fr_1', 'fr_2'],
        'put_accent': False,
        'put_yo': False
    },
    'Ukrainian': {
        'lang': 'ua',
        'model': 'v4_ua',
        'speakers': ['mykyta'],
        'put_accent': False,
        'put_yo': False
    },
    'Bashkir': {
        'lang': 'ba',
        'model': 'aigul_v2',
        'speakers': ['aigul'],
        'put_accent': False,
        'put_yo': False
    },
    'Kalmyk': {
        'lang': 'xal',
        'model': 'v3_xal',
        'speakers': ['erdni'],
        'put_accent': False,
        'put_yo': False
    },
    'Tatar': {
        'lang': 'tt',
        'model': 'v3_tt',
        'speakers': ['dilyara'],
        'put_accent': False,
        'put_yo': False
    },
    'Uzbek': {
        'lang': 'uz',
        'model': 'v4_uz',
        'speakers': ['dilnavoz'],
        'put_accent': False,
        'put_yo': False
    },
    'Indic': {
        'lang': 'indic',
        'model': 'v4_indic',
        'speakers': ['indic'],
        'put_accent': False,
        'put_yo': False
    },
    'Cyrillic': {
        'lang': 'cyr',
        'model': 'v4_cyrillic',
        'speakers': ['cyrillic'],
        'put_accent': False,
        'put_yo': False
    },
}
loaded_models = {}


def get_speakers(language):
    return LANGUAGES[language]['speakers']


def load_model(language):
    if language in loaded_models:
        return loaded_models[language]

    lang_cfg = LANGUAGES[language]
    print(f"[INFO] Loading model for {language} ({lang_cfg['model']})...")

    model, example_text = torch.hub.load(
        repo_or_dir='snakers4/silero-models',
        model='silero_tts',
        language=lang_cfg['lang'],
        speaker=lang_cfg['model'],
        device=device,
        trust_repo=True
    )

    model.to(device)
    loaded_models[language] = model
    print(f"[INFO] Model for {language} loaded successfully")
    return model


def synthesize(text, language, speaker, text_type, sample_rate=48000):
    if not text or not text.strip():
        return None, "Введите какой-нибудь текст"

    try:
        model = load_model(language)
        lang_cfg = LANGUAGES[language]

        # Validate speaker
        if hasattr(model, 'speakers') and model.speakers:
            available_speakers = model.speakers
            if isinstance(available_speakers, dict):
                available_speakers = list(available_speakers.keys())
            if speaker not in available_speakers:
                return None, f"Ошибка: Диктор '{speaker}' не найден. Доступны дикторы: {available_speakers}"

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"silero_{lang_cfg['lang']}_{speaker}_{sample_rate}hz_{timestamp}.wav"
        output_path = os.path.join(outputs_dir, output_filename)

        # SSML or plain text
        if text_type == "SSML":
            model.save_wav(
                audio_path=output_path,
                ssml_text=text,
                speaker=speaker,
                sample_rate=sample_rate,
                put_accent=lang_cfg.get('put_accent', False),
                put_yo=lang_cfg.get('put_yo', False)
            )
        else:
            model.save_wav(
                audio_path=output_path,
                text=text,
                speaker=speaker,
                sample_rate=sample_rate,
                put_accent=lang_cfg.get('put_accent', False),
                put_yo=lang_cfg.get('put_yo', False)
            )

        device_info = str(device)
        if device.type == 'cuda':
            device_info += f" ({torch.cuda.get_device_name(0)})"

        ssml_info = " | SSML" if text_type == "SSML" else ""

        return output_path, f"✓ Файл записан в папку outputs/{output_filename}{ssml_info} | {language}/{speaker} @ {sample_rate}Hz на {device_info}"

    except Exception as e:
        return None, f"Ошибка: {str(e)}"


def update_speakers(language):
    speakers = get_speakers(language)
    return gr.Dropdown(choices=speakers, value=speakers[0])

# === Custom CSS to fix audio seek bar overlapping time ===
custom_css = """
/* Fix audio player time display overlap for long audio */
.audio-output {
    padding-bottom: 25px !important;
}
.audio-output audio {
    min-height: 75px !important;
}
/* Gradio 4.x+ audio component */
[data-testid="audio"] {
    padding-bottom: 20px !important;
}
[data-testid="audio"] audio {
    min-height: 70px !important;
}
/* Waveform container padding */
.waveform-container {
    margin-bottom: 15px !important;
}
"""

# === Build Gradio interface ===
with gr.Blocks(title="Silero TTS Portable", css=custom_css) as demo:
    gr.Markdown("""
    # 🗣️ Silero текст-в-речь ===> автор сборки: [NeiroVlad](https://oti.by)
    Портативная версия TTS на базе моделей Silero. При первом запуске модели скачиваются и сохраняются в папку `cache/torch`.
    """)

    gr.Markdown(f"**Устройство:** `{device}`" + (f" — `{torch.cuda.get_device_name(0)}`" if device.type == 'cuda' else ""))

    with gr.Row():
        with gr.Column(scale=1):
            language = gr.Dropdown(
                choices=list(LANGUAGES.keys()),
                value='Russian',
                label="🌐 Язык"
            )
            speaker = gr.Dropdown(
                choices=get_speakers('Russian'),
                value='xenia',
                label="🎙️ Диктор"
            )
            sample_rate = gr.Radio(
                choices=[8000, 16000, 24000, 48000],
                value=48000,
                label="📊 Частота дискретизации"
            )
            text_type = gr.Radio(
                choices=["Common", "SSML"],
                value="Common",
                label="📝 Тип текста",
                info="SSML поддерживает паузы, ударения, фонемы ..."
            )
            text_input = gr.Textbox(
                label="Текст или SSML для генерации",
                placeholder="Введите текст... Пример для SSML: <speak>Hello <break time='500ms'/> world</speak>",
                lines=10,
                max_lines=30
            )
            submit_btn = gr.Button("🚀 Генерировать", variant="primary", size="lg")

        with gr.Column(scale=1):
            audio_output = gr.Audio(
                label="🔊 Созданный файл",
                type="filepath",
                autoplay=False,
                elem_classes="audio-output"
            )
            status = gr.Textbox(
                label="📋 Статус",
                interactive=False,
                value="Готов"
            )

            gr.Markdown("""
            ### 💡 Пример SSML на русском языке
            ```xml
            <speak>
              В недрах тундры выдры в г+етрах 
              т+ырят в вёдра ядра к+едров.
              <break time="500ms"/>
              П+ока!
            </speak>
            ```

            ### 💡 Советы
            - `+` перед ударной гласной (например, `г+етрах`)
            - `<break time="500ms"/>` = пауза
            - Готовые фалы сохраняются в папку `outputs/`
            - При первом запуске или первом выборе другого языка нужно скачать ~100-300MB
            """)

            gr.Markdown(
                """[Официальная документация](https://github.com/snakers4/silero-models/wiki/SSML) по формату SSML."""
            )

    language.change(
        fn=update_speakers,
        inputs=language,
        outputs=speaker
    )

    submit_btn.click(
        fn=synthesize,
        inputs=[text_input, language, speaker, text_type, sample_rate],
        outputs=[audio_output, status]
    )

    # === Authors section at the bottom ===
    gr.Markdown("---")
    gr.Markdown("""
    <div align="center">

    ### Ссылки на авторов

    - **NeiroVlad** ([github.com/vlad-ir](https://github.com/vlad-ir)) — автор портабельной сборки
    - **oti.by** ([t.me/vlad_vlk](https://t.me/vlad_vlk)) — [oti.by](https://oti.by) — нейронные сети и умные чат-боты для бизнеса
    - **Нейронки в бизнесе и в жизни** ([t.me/neiro_com](https://t.me/neiro_com)) — промпты, примеры, советы и т.д.
    - **Silero Team** ([github.com/snakers4](https://github.com/snakers4)) — авторы моделей TTS
    - **NeuroSenko** ([huggingface.co/spaces/NeuroSenko](https://huggingface.co/spaces/NeuroSenko/tts-silero/tree/main)) — демо-версия Silero

    </div>
    """)

if __name__ == "__main__":
    print(f"[INFO] Starting Silero TTS on http://127.0.0.1:8891")
    demo.launch(
        server_name="127.0.0.1",
        server_port=8891,
        share=False,
        show_error=True,
        inbrowser=True  # Автоматически открывает браузер после старта сервера
    )
