
import os
import re
import time
import unicodedata

from google import genai

from memory.memory import (
    crear_memoria,
    guardar_recuerdo,
    buscar_recuerdo,
    obtener_recuerdos,
    olvidar_recuerdo,
    guardar_mensaje_chat,
    obtener_mensajes_chat,
)


# =========================================================
# CONFIGURACIÓN
# =========================================================

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODELO_NOVA = "gemini-3.6-flash"

INSTRUCCIONES_NOVA = """
Eres NOVA (Neural Operations & Virtual Assistant),
un asistente virtual académico para estudiantes de
Ingeniería en Sistemas Computacionales.

Responde principalmente en español, con claridad,
paciencia, amabilidad y un toque de humor cuando sea apropiado.

Ayuda a comprender programación, algoritmos, bases de datos,
redes, sistemas operativos y otras materias relacionadas.

Explica paso a paso cuando sea necesario.
No inventes información ni recuerdos.

Los recuerdos y las conversaciones pertenecen únicamente
al usuario autenticado de la conversación actual.
Nunca afirmes conocer datos que no estén disponibles.
"""

crear_memoria()


# =========================================================
# UTILIDADES
# =========================================================

def normalizar_clave(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    texto = re.sub(r"[^a-z0-9_\- ]", "", texto)
    texto = re.sub(r"\s+", "_", texto)

    return texto.strip("_")


def guardar_intercambio(uid, chat_id, comando, respuesta):
    guardar_mensaje_chat(
        uid, chat_id, "usuario", comando
    )

    guardar_mensaje_chat(
        uid, chat_id, "nova", respuesta
    )


def construir_historial(mensajes):
    historial = []

    for mensaje in mensajes:
        rol = mensaje.get("rol")
        contenido = mensaje.get("contenido", "")

        if not contenido or rol not in ("usuario", "nova"):
            continue

        historial.append({
            "role": "user" if rol == "usuario" else "model",
            "parts": [{"text": contenido}],
        })

    return historial


# =========================================================
# RECUERDOS
# =========================================================

def detectar_recuerdo(comando, uid):
    coincidencia = re.match(
        r"^recuerda\s+que\s+(.+)$",
        comando.strip(),
        flags=re.IGNORECASE,
    )

    if not coincidencia:
        return None

    contenido = coincidencia.group(1).strip()

    partes = re.split(
        r"\s+es\s+|\s*:\s*",
        contenido,
        maxsplit=1,
        flags=re.IGNORECASE,
    )

    if len(partes) == 2:
        clave = normalizar_clave(partes[0])
        valor = partes[1].strip()
    else:
        clave = "nota_" + str(int(time.time() * 1000))
        valor = contenido

    if not clave or not valor:
        return "Necesito una clave y un dato para guardar el recuerdo."

    guardar_recuerdo(uid, clave, valor)

    return f"Listo, recordaré para tu cuenta: {valor}"


def mostrar_memoria(uid):
    recuerdos = obtener_recuerdos(uid)

    if not recuerdos:
        return "Todavía no tienes recuerdos guardados en tu cuenta."

    lineas = [
        f"- {clave}: {valor}"
        for clave, valor in recuerdos
    ]

    return "Estos son tus recuerdos:\n" + "\n".join(lineas)


# =========================================================
# PROCESAR COMANDOS
# =========================================================

def procesar_comando(comando, uid, chat_id):
    if not uid:
        raise ValueError("No se recibió el UID del usuario.")

    if not chat_id:
        raise ValueError("No se recibió el ID de la conversación.")

    comando = (comando or "").strip()

    if not comando:
        return "Escribe un mensaje para que podamos comenzar."

    texto = comando.lower().strip()

    # -----------------------------------------------------
    # Guardar un recuerdo
    # -----------------------------------------------------

    respuesta = detectar_recuerdo(comando, uid)

    if respuesta is not None:
        guardar_intercambio(uid, chat_id, comando, respuesta)
        return respuesta

    # -----------------------------------------------------
    # Mostrar recuerdos
    # -----------------------------------------------------

    comandos_memoria = {
        "mis recuerdos",
        "mostrar recuerdos",
        "qué recuerdas de mí",
        "que recuerdas de mi",
        "qué recuerdas",
        "que recuerdas",
    }

    if texto in comandos_memoria:
        respuesta = mostrar_memoria(uid)
        guardar_intercambio(uid, chat_id, comando, respuesta)
        return respuesta

    # -----------------------------------------------------
    # Buscar un recuerdo
    # -----------------------------------------------------

    coincidencia = re.match(
        r"^(?:busca|buscar|recuerda)\s+"
        r"(?:el recuerdo\s+)?(.+)$",
        texto,
        flags=re.IGNORECASE,
    )

    if coincidencia:
        clave = normalizar_clave(coincidencia.group(1))
        valor = buscar_recuerdo(uid, clave)

        if valor is not None:
            respuesta = f"Encontré este recuerdo: {valor}"
            guardar_intercambio(uid, chat_id, comando, respuesta)
            return respuesta

    # -----------------------------------------------------
    # Olvidar un recuerdo
    # -----------------------------------------------------

    coincidencia = re.match(
        r"^(?:olvida|borrar recuerdo|elimina recuerdo)\s+(.+)$",
        texto,
        flags=re.IGNORECASE,
    )

    if coincidencia:
        clave = normalizar_clave(coincidencia.group(1))
        valor = buscar_recuerdo(uid, clave)

        if valor is None:
            respuesta = "No encontré ese recuerdo en tu cuenta."
        else:
            olvidar_recuerdo(uid, clave)
            respuesta = (
                f"Listo, eliminé de tu cuenta el recuerdo '{clave}'."
            )

        guardar_intercambio(uid, chat_id, comando, respuesta)
        return respuesta

    # -----------------------------------------------------
    # Recuperar el historial de esta conversación
    # -----------------------------------------------------

    mensajes = obtener_mensajes_chat(uid, chat_id)
    historial = construir_historial(mensajes)

    # -----------------------------------------------------
    # Contexto de recuerdos del usuario actual
    # -----------------------------------------------------

    recuerdos = obtener_recuerdos(uid)
    mensaje_modelo = comando

    if recuerdos:
        contexto = "\n".join(
            f"- {clave}: {valor}"
            for clave, valor in recuerdos
        )

        mensaje_modelo = (
            "Utiliza estos recuerdos como contexto del usuario "
            "autenticado. No los confundas con información "
            "de otras personas.\n\n"
            f"Recuerdos:\n{contexto}\n\n"
            f"Mensaje del usuario:\n{comando}"
        )

    # -----------------------------------------------------
    # Consultar Gemini con el historial recuperado
    # -----------------------------------------------------

    chat_usuario = client.chats.create(
        model=MODELO_NOVA,
        config={
            "system_instruction": INSTRUCCIONES_NOVA,
        },
        history=historial,
    )

    for intento in range(3):
        try:
            resultado = chat_usuario.send_message(
                mensaje_modelo
            )

            respuesta = (
                resultado.text
                or "No pude generar una respuesta."
            )

            break

        except Exception as error:
            error_texto = str(error).lower()

            error_temporal = (
                "503" in error_texto
                or "unavailable" in error_texto
                or "overloaded" in error_texto
            )

            if error_temporal and intento < 2:
                time.sleep(2 * (intento + 1))
                continue

            raise

    # Guardar el intercambio una sola vez después de obtener
    # una respuesta correcta del modelo.
    guardar_intercambio(
        uid,
        chat_id,
        comando,
        respuesta,
    )

    return respuesta
