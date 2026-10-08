import os
from elevenlabs.client import ElevenLabs

api_key = os.getenv("ELEVENLABS_API_KEY")
voice_id = os.getenv("ELEVENLABS_VOICE_ID")

client = ElevenLabs(api_key=api_key)

audio = client.text_to_speech.convert(
    voice_id=voice_id,
    text="Hola José. Soy NOVA. Todos mis sistemas están funcionando correctamente.",
    model_id="eleven_multilingual_v2"
)

with open("nova_prueba.mp3", "wb") as archivo:
    for fragmento in audio:
        archivo.write(fragmento)

print("✅ Audio generado correctamente: nova_prueba.mp3")