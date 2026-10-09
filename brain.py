from google import genai
import os
import re
import time

from memory.memory import (
    crear_memoria,
    guardar_recuerdo,
    buscar_recuerdo,
    obtener_recuerdos,
    olvidar_recuerdo
)


# =========================================================
# CONEXIÓN CON GEMINI
# =========================================================

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


# =========================================================
# PERSONALIDAD DE NOVA
# =========================================================

INSTRUCCIONES_NOVA = """
Tu nombre es NOVA.

NOVA significa:
Neural Operations & Virtual Assistant.

Eres un asistente virtual académico especializado en
estudiantes de Ingeniería en Sistemas Computacionales.

Tu objetivo principal es ayudar al estudiante a aprender,
comprender programación y desarrollar sus propios proyectos.

=========================================================
PERSONALIDAD
=========================================================

Eres:

- Inteligente.
- Amable.
- Natural.
- Paciente.
- Servicial.
- Curiosa.
- Clara.
- Con un pequeño toque de humor cuando sea apropiado.

Hablas principalmente en español.

No hables como un robot.

Tu nombre es NOVA, no Gemini.

=========================================================
MODO TUTOR
=========================================================

Tu función principal es enseñar.

Cuando el estudiante pregunte sobre un tema que no
comprende:

1. Explica primero el concepto de forma sencilla.
2. Utiliza ejemplos fáciles de entender.
3. Después aumenta gradualmente la dificultad.
4. Si corresponde, utiliza código.
5. Explica el código línea por línea cuando sea necesario.
6. Comprueba si existe algún error de comprensión.
7. Si es apropiado, termina con un pequeño ejercicio.

No asumas conocimientos que el estudiante no haya demostrado.

Si el estudiante dice:

"no entiendo"

"explícamelo"

"no sé cómo hacerlo"

"no entiendo este código"

entonces utiliza una explicación más sencilla.

=========================================================
APRENDIZAJE ACTIVO
=========================================================

No debes resolver siempre todo inmediatamente.

Si el estudiante quiere aprender:

- Puedes darle pistas.
- Puedes hacerle preguntas.
- Puedes darle ejercicios.
- Puedes revisar sus respuestas.
- Puedes corregir sus errores.
- Puedes explicarle por qué una respuesta es incorrecta.

Si el estudiante pide explícitamente la solución completa,
puedes proporcionarla.

=========================================================
PROGRAMACIÓN
=========================================================

Puedes ayudar con:

Python
C
C++
C#
Java
JavaScript
TypeScript
PHP
SQL
HTML
CSS

También:

React
Next.js
Node.js
APIs
MySQL
SQL Server
PostgreSQL
Git
GitHub
Algoritmos
Estructuras de datos
Programación orientada a objetos
Desarrollo web
Redes
Sistemas operativos
Ciberseguridad

=========================================================
CÓDIGO
=========================================================

Cuando el estudiante proporcione código:

1. Identifica el problema.
2. Explica por qué ocurre.
3. Indica exactamente dónde está.
4. Muestra la corrección.
5. Explica qué cambió.

No modifiques código que no sea necesario modificar.

Distingue entre:

"Corrección necesaria"

y

"Mejora opcional".

=========================================================
PROYECTOS
=========================================================

Cuando el estudiante esté trabajando en un proyecto:

- Respeta su estructura.
- Respeta las tecnologías que ya utiliza.
- No elimines funcionalidades existentes.
- No cambies tecnologías sin una razón.
- Trabaja sobre el código existente.
- Explica los cambios importantes.

=========================================================
EJERCICIOS
=========================================================

Cuando el estudiante pida un ejercicio:

- Indica claramente el objetivo.
- Explica las reglas.
- No des inmediatamente la solución.
- Permite que el estudiante intente resolverlo.

Si pide una pista:

Da solamente una pista útil.

Si pide la solución:

Entonces proporciona la solución y explica el procedimiento.

=========================================================
EXÁMENES
=========================================================

Si el estudiante pide un examen:

- Haz preguntas relacionadas con el tema.
- Una pregunta a la vez.
- Espera la respuesta del estudiante.
- Indica si es correcta o incorrecta.
- Explica la respuesta.
- Continúa con la siguiente pregunta.

=========================================================
MEMORIA
=========================================================

Utiliza los recuerdos proporcionados por el sistema cuando
sean relevantes.

No inventes recuerdos.

Si no tienes una información guardada,
dilo honestamente.

=========================================================
OBJETIVO
=========================================================

Tu objetivo no es simplemente darle respuestas al estudiante.

Tu objetivo es ayudarlo a aprender para que posteriormente
pueda resolver problemas por sí mismo.
"""


# =========================================================
# INICIAR MEMORIA
# =========================================================

crear_memoria()


# =========================================================
# CREAR CHAT
# =========================================================

chat = client.chats.create(
    model="gemini-3.6-flash",
    config={
        "system_instruction": INSTRUCCIONES_NOVA
    }
)


# =========================================================
# NORMALIZAR CLAVES
# =========================================================

def normalizar_clave(texto):

    texto = texto.lower().strip()

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n"
    }

    for original, nuevo in reemplazos.items():
        texto = texto.replace(original, nuevo)

    texto = re.sub(
        r"[^a-z0-9\s]",
        "",
        texto
    )

    texto = re.sub(
        r"\s+",
        "_",
        texto
    )

    return texto


# =========================================================
# DETECTAR RECUERDO
# =========================================================

def detectar_recuerdo(comando):

    texto = comando.strip()

    texto_lower = texto.lower()


    if texto_lower.startswith("recuerda que "):

        contenido = texto[12:].strip()

        if contenido:

            coincidencia = re.match(
                r"mi (.+?) es (.+)",
                contenido,
                re.IGNORECASE
            )

            if coincidencia:

                clave = coincidencia.group(1).strip()
                valor = coincidencia.group(2).strip()

                clave = normalizar_clave(clave)

                if clave and valor:

                    guardar_recuerdo(
                        clave,
                        valor
                    )

                    return (
                        f"Perfecto. Guardaré que "
                        f"{clave.replace('_', ' ')} "
                        f"es {valor}."
                    )

            clave = "dato_" + str(
                len(obtener_recuerdos()) + 1
            )

            guardar_recuerdo(
                clave,
                contenido
            )

            return (
                "Perfecto. Lo guardaré en mi memoria."
            )


    coincidencia = re.match(
        r"mi (.+?) es (.+)",
        texto,
        re.IGNORECASE
    )

    if coincidencia:

        clave = coincidencia.group(1).strip()
        valor = coincidencia.group(2).strip()

        clave = normalizar_clave(clave)

        if clave and valor:

            guardar_recuerdo(
                clave,
                valor
            )

            return (
                f"Entendido. Recordaré que "
                f"{clave.replace('_', ' ')} "
                f"es {valor}."
            )

    return None


# =========================================================
# MOSTRAR MEMORIA
# =========================================================

def mostrar_memoria():

    recuerdos = obtener_recuerdos()

    if not recuerdos:

        return (
            "Todavía no tengo recuerdos guardados."
        )

    respuesta = (
        "Esto es lo que recuerdo de ti:\n\n"
    )

    for clave, valor in recuerdos:

        nombre = clave.replace(
            "_",
            " "
        )

        respuesta += (
            f"• {nombre}: {valor}\n"
        )

    return respuesta


# =========================================================
# PROCESAR COMANDOS
# =========================================================

def procesar_comando(comando):

    texto = comando.lower().strip()


    # =====================================================
    # MOSTRAR MEMORIA
    # =====================================================

    if (
        "qué recuerdas de mí" in texto
        or "que recuerdas de mi" in texto
        or "qué recuerdas" in texto
        or "que recuerdas" in texto
        or "muéstrame tu memoria" in texto
        or "muestrame tu memoria" in texto
    ):

        return mostrar_memoria()


    # =====================================================
    # OLVIDAR RECUERDO
    # =====================================================

    if texto.startswith("olvida mi "):

        clave = comando[9:].strip()

        clave = normalizar_clave(
            clave
        )

        if buscar_recuerdo(clave):

            olvidar_recuerdo(
                clave
            )

            return (
                f"Listo. He olvidado tu "
                f"{clave.replace('_', ' ')}."
            )

        return (
            "No encontré ese recuerdo "
            "en mi memoria."
        )


    # =====================================================
    # DETECTAR NUEVO RECUERDO
    # =====================================================

    recuerdo = detectar_recuerdo(
        comando
    )

    if recuerdo:

        return recuerdo


    # =====================================================
    # RECUPERAR MEMORIA
    # =====================================================

    recuerdos = obtener_recuerdos()

    contexto = ""

    if recuerdos:

        contexto = """
Información que NOVA recuerda del estudiante:

"""

        for clave, valor in recuerdos:

            nombre = clave.replace(
                "_",
                " "
            )

            contexto += (
                f"- {nombre}: {valor}\n"
            )


    # =====================================================
    # MENSAJE PARA NOVA
    # =====================================================

    mensaje = f"""
{contexto}

Mensaje del estudiante:

{comando}
"""


    # =====================================================
    # GEMINI
    # =====================================================

    max_intentos = 3

    for intento in range(
        max_intentos
    ):

        try:

            respuesta = chat.send_message(
                mensaje
            )

            return respuesta.text


        except Exception as error:

            print(
                f"[ERROR GEMINI] {error}"
            )

            error_texto = str(
                error
            ).upper()


            if (
                "503" in error_texto
                or "UNAVAILABLE" in error_texto
            ):

                if intento < max_intentos - 1:

                    espera = 2 * (
                        intento + 1
                    )

                    print(
                        f"NOVA reintentará "
                        f"en {espera} segundos..."
                    )

                    time.sleep(
                        espera
                    )

                    continue

            break


    return (
        "Tuve un problema temporal para "
        "conectarme con mi cerebro. "
        "Intenta nuevamente en unos segundos."
    )