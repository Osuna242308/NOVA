import os
import sounddevice as sd
from scipy.io.wavfile import write
from google import genai

from core.brain import procesar_comando


FRECUENCIA = 16000
DURACION = 5
ARCHIVO = "voz_nova.wav"


def grabar_audio():
    print("🎙️ NOVA está escuchando...")

    audio = sd.rec(
        int(DURACION * FRECUENCIA),
        samplerate=FRECUENCIA,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    write(ARCHIVO, FRECUENCIA, audio)

    print("✅ Grabación terminada.")


def transcribir_audio():
    print("🧠 NOVA está procesando tu voz...")

    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY")
    )

    archivo = client.files.upload(file=ARCHIVO)

    respuesta = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            archivo,
            "Transcribe exactamente lo que se dice en este audio. "
            "Devuelve solamente el texto transcrito, sin explicaciones."
        ]
    )

    return respuesta.text.strip()


if __name__ == "__main__":

    grabar_audio()

    texto = transcribir_audio()

    print()
    print(f"📝 Tú dijiste: {texto}")
    print()

    respuesta = procesar_comando(texto)

    print(f"🤖 NOVA: {respuesta}")