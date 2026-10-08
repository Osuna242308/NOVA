import os
import tempfile
from elevenlabs.client import ElevenLabs
from playsound3 import playsound


def hablar(texto):

    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "").strip()

    if not api_key:
        print("❌ No se encontró ELEVENLABS_API_KEY")
        return

    if not voice_id:
        print("❌ No se encontró ELEVENLABS_VOICE_ID")
        return

    archivo = None

    try:

        client = ElevenLabs(
            api_key=api_key
        )

        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=texto,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )

        audio_bytes = b"".join(audio)

        with tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        ) as temp:

            temp.write(audio_bytes)
            archivo = temp.name

        playsound(archivo)

    except Exception as error:

        print(f"❌ Error en la voz de NOVA: {error}")

    finally:

        if archivo and os.path.exists(archivo):

            try:
                os.remove(archivo)
            except:
                pass


if __name__ == "__main__":

    hablar(
        "Hola José. Soy NOVA. "
        "Mi sistema de voz está funcionando correctamente."
    )