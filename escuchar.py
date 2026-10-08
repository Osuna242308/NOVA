import sounddevice as sd
import speech_recognition as sr
import wave
import tempfile
import os
import numpy as np


FRECUENCIA = 16000
CANALES = 1

CALIBRACION = 2.0
SILENCIO_MAXIMO = 1.5

BLOQUE = 0.1

# Sensibilidad del micrófono
# Menor = detecta voces más bajas
SENSIBILIDAD = 1.8

# Límites para evitar que el ruido eleve demasiado el umbral
UMBRAL_MINIMO = 0.008
UMBRAL_MAXIMO = 0.035

# Cantidad de bloques necesarios para confirmar que es voz
BLOQUES_VOZ = 4


def volumen_audio(audio):
    return np.sqrt(np.mean(audio ** 2))


def escuchar():

    try:

        print("Calibrando micrófono...")
        print("No hables durante la calibración.")

        with sd.InputStream(
            samplerate=FRECUENCIA,
            channels=CANALES,
            dtype="float32"
        ) as stream:

            muestras = []

            cantidad_bloques = int(
                CALIBRACION / BLOQUE
            )

            for _ in range(cantidad_bloques):

                audio, _ = stream.read(
                    int(BLOQUE * FRECUENCIA)
                )

                muestras.append(audio.copy())

            ruido = np.concatenate(
                muestras,
                axis=0
            )

            ruido_ambiente = volumen_audio(ruido)

            umbral = ruido_ambiente * SENSIBILIDAD

            umbral = max(
                UMBRAL_MINIMO,
                min(umbral, UMBRAL_MAXIMO)
            )

            print(
                f"Ruido ambiente: {ruido_ambiente:.4f}"
            )

            print(
                f"Umbral de voz: {umbral:.4f}"
            )

            print("Nova está escuchando...")

            bloques = []

            hablando = False
            bloques_voz = 0
            silencio = 0

            while True:

                audio, _ = stream.read(
                    int(BLOQUE * FRECUENCIA)
                )

                audio = audio.copy()

                nivel = volumen_audio(audio)

                # Detectar voz
                if nivel > umbral:

                    bloques_voz += 1

                else:

                    bloques_voz = 0

                # Esperar hasta confirmar que realmente empezó a hablar
                if not hablando:

                    if bloques_voz >= BLOQUES_VOZ:

                        hablando = True

                        print("Voz detectada...")

                        # Guardamos el bloque actual
                        bloques.append(audio)

                    continue

                # Guardar todo el audio mientras habla
                bloques.append(audio)

                if nivel > umbral:

                    silencio = 0

                else:

                    silencio += BLOQUE

                    if silencio >= SILENCIO_MAXIMO:

                        print("Silencio detectado.")

                        break

        if not hablando:

            print("No se detectó voz.")

            return None

        # Unir todos los bloques
        audio_completo = np.concatenate(
            bloques,
            axis=0
        )

        # Crear archivo temporal WAV
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as archivo:

            nombre_archivo = archivo.name

        with wave.open(
            nombre_archivo,
            "wb"
        ) as wav:

            wav.setnchannels(CANALES)
            wav.setsampwidth(2)
            wav.setframerate(FRECUENCIA)

            audio_int16 = (
                audio_completo * 32767
            ).astype(np.int16)

            wav.writeframes(
                audio_int16.tobytes()
            )

        print("Procesando voz...")

        reconocedor = sr.Recognizer()

        with sr.AudioFile(
            nombre_archivo
        ) as fuente:

            audio_grabado = reconocedor.record(
                fuente
            )

        texto = reconocedor.recognize_google(
            audio_grabado,
            language="es-MX"
        )

        print(f"Dijiste: {texto}")

        os.remove(nombre_archivo)

        return texto

    except sr.UnknownValueError:

        print("No pude entender lo que dijiste.")

        return None

    except sr.RequestError as error:

        print(
            f"Error del reconocimiento: {error}"
        )

        return None

    except Exception as error:

        print(f"Error: {error}")

        return None


if __name__ == "__main__":

    while True:

        texto = escuchar()

        if texto and texto.lower() in [
                   "salir",
                   "terminar",
                   "cerrar"
               ]:
       
                   print("Prueba terminada.")
       
                   break