from core.brain import procesar_comando
from escuchar import escuchar
from hablar import hablar


print("=" * 40)
print("           N.O.V.A.")
print("   Neural Operations & Virtual Assistant")
print("=" * 40)
print("NOVA: Sistema iniciado correctamente.")
print()


while True:

    texto = escuchar()

    if not texto:
        continue

    comando = texto.lower().strip()

    if any(palabra in comando for palabra in [
        "salir",
        "terminar",
        "cerrar"
    ]):

        hablar("Hasta luego, José.")
        print("NOVA: Hasta luego.")
        break

    print()
    print("🧠 NOVA está pensando...")

    try:

        respuesta = procesar_comando(texto)

        print(f"NOVA: {respuesta}")

        hablar(respuesta)

    except Exception as error:

        print(f"Error: {error}")

        hablar(
            "Ocurrió un error al procesar tu solicitud."
        )