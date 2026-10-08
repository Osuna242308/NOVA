import sounddevice as sd

print("🎙️ Probando micrófono...")
print("Habla durante 5 segundos...")

audio = sd.rec(
    int(5 * 16000),
    samplerate=16000,
    channels=1,
    dtype="int16",
    device=1
)

sd.wait()

print("✅ Grabación terminada.")
print("NOVA pudo acceder al micrófono correctamente.")