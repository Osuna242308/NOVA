
import os
import uuid
from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.brain import procesar_comando
from memory.memory import (
    obtener_chats,
    obtener_mensajes_chat,
    obtener_tareas,
    crear_tarea,
    actualizar_tarea,
    eliminar_tarea,
    obtener_notas,
    crear_nota,
    actualizar_nota,
    eliminar_nota,
)


# =========================================================
# CONFIGURACIÓN
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"


def iniciar_firebase():
    if not firebase_admin._apps:
        ruta = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not ruta or not os.path.isfile(ruta):
            raise RuntimeError(
                "No se encontró un archivo válido en "
                "GOOGLE_APPLICATION_CREDENTIALS."
            )

        credencial = credentials.Certificate(ruta)
        firebase_admin.initialize_app(credencial)


iniciar_firebase()


app = FastAPI(
    title="N.O.V.A.",
    description="Neural Operations & Virtual Assistant",
    version="1.4.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


if STATIC_DIR.is_dir():
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )


# =========================================================
# MODELOS
# =========================================================

class Mensaje(BaseModel):
    mensaje: str
    chat_id: str | None = None
    tasks: list[dict] = []


class NuevaTarea(BaseModel):
    text: str


class ActualizarTarea(BaseModel):
    text: str | None = None
    done: bool | None = None


class NuevaNota(BaseModel):
    title: str = ""
    body: str = ""


class ActualizarNota(BaseModel):
    title: str | None = None
    body: str | None = None


# =========================================================
# AUTENTICACIÓN
# =========================================================

def obtener_uid(authorization: str | None) -> str:
    if (
        not authorization
        or not authorization.startswith("Bearer ")
    ):
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión para usar NOVA.",
        )

    token = authorization.split(" ", 1)[1].strip()

    try:
        usuario = auth.verify_id_token(token)
        return usuario["uid"]

    except Exception:
        raise HTTPException(
            status_code=401,
            detail=(
                "Tu sesión no es válida. "
                "Inicia sesión nuevamente."
            ),
        )


# =========================================================
# PÁGINA PRINCIPAL
# =========================================================

@app.get("/", include_in_schema=False)
def inicio():
    if INDEX_FILE.is_file():
        return FileResponse(str(INDEX_FILE))

    return {
        "nombre": "N.O.V.A.",
        "estado": "en linea",
        "mensaje": "Falta static/index.html.",
    }


@app.get("/health")
def salud():
    return {"estado": "ok"}


# =========================================================
# ENVIAR MENSAJES A NOVA
# =========================================================

@app.post("/chat")
def chat(
    datos: Mensaje,
    authorization: str | None = Header(default=None),
):
    uid = obtener_uid(authorization)

    if not datos.mensaje.strip():
        raise HTTPException(
            status_code=400,
            detail="El mensaje no puede estar vacío.",
        )

    chat_id = datos.chat_id or str(uuid.uuid4())

    try:
        respuesta = procesar_comando(
            datos.mensaje,
            uid,
            chat_id,
            datos.tasks,
        )

        return {
            "respuesta": str(respuesta),
            "chat_id": chat_id,
        }

    except Exception as error:
        print(f"Error al procesar el mensaje de NOVA: {error}")

        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudo procesar el mensaje. "
                "Revisa los registros del servidor."
            ),
        )


# =========================================================
# CONVERSACIONES
# =========================================================

@app.get("/chats")
def listar_chats(
    authorization: str | None = Header(default=None),
):
    uid = obtener_uid(authorization)

    try:
        return {
            "chats": obtener_chats(uid),
        }

    except Exception as error:
        print(f"Error al recuperar conversaciones: {error}")

        raise HTTPException(
            status_code=500,
            detail="No se pudieron recuperar las conversaciones.",
        )


@app.get("/chats/{chat_id}/mensajes")
def listar_mensajes(
    chat_id: str,
    authorization: str | None = Header(default=None),
):
    uid = obtener_uid(authorization)

    try:
        mensajes = obtener_mensajes_chat(uid, chat_id)

        return {
            "chat_id": chat_id,
            "mensajes": mensajes,
        }

    except Exception as error:
        print(f"Error al recuperar mensajes de NOVA: {error}")

        raise HTTPException(
            status_code=500,
            detail="No se pudieron recuperar los mensajes.",
        )


# =========================================================
# TAREAS
# =========================================================

@app.get("/tareas")
def listar_tareas(
    authorization: str | None = Header(default=None),
):
    uid = obtener_uid(authorization)

    try:
        return {"tareas": obtener_tareas(uid)}

    except Exception as error:
        print(f"Error al recuperar tareas: {error}")
        raise HTTPException(
            status_code=500,
            detail="No se pudieron recuperar las tareas.",
        )


@app.post("/tareas")
def agregar_tarea(
    datos: NuevaTarea,
    authorization: str | None = Header(default=None),
):
    uid = obtener_uid(authorization)

    try:
        tarea = crear_tarea(uid, datos.text)
        return {"tarea": tarea}

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        print(f"Error al crear tarea: {error}")
        raise HTTPException(
            status_code=500,
            detail="No se pudo crear la tarea.",
        )


@app.patch("/tareas/{tarea_id}")
def modificar_tarea(
    tarea_id: str,
    datos: ActualizarTarea,
    authorization: str | None = Header(default=None),
):
    uid = obtener_uid(authorization)

    try:
        actualizar_tarea(
            uid,
            tarea_id,
            texto=datos.text,
            done=datos.done,
        )

        return {"mensaje": "Tarea actualizada."}

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except Exception as error:
        print(f"Error al actualizar tarea: {error}")
        raise HTTPException(
            status_code=500,
            detail="No se pudo actualizar la tarea.",
        )


@app.delete("/tareas/{tarea_id}")
def borrar_tarea(
    tarea_id: str,
    authorization: str | None = Header(default=None),
):
    uid = obtener_uid(authorization)

    try:
        eliminar_tarea(uid, tarea_id)
        return {"mensaje": "Tarea eliminada."}

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except Exception as error:
        print(f"Error al eliminar tarea: {error}")
        raise HTTPException(
            status_code=500,
            detail="No se pudo eliminar la tarea.",
        )


# =========================================================
# NOTAS
# =========================================================

@app.get("/notas")
def listar_notas(
    authorization: str | None = Header(default=None),
):
    uid = obtener_uid(authorization)

    try:
        return {"notas": obtener_notas(uid)}

    except Exception as error:
        print(f"Error al recuperar notas: {error}")
        raise HTTPException(
            status_code=500,
            detail="No se pudieron recuperar las notas.",
        )


@app.post("/notas")
def agregar_nota(
    datos: NuevaNota,
    authorization: str | None = Header(default=None),
):
    uid = obtener_uid(authorization)

    try:
        nota = crear_nota(uid, datos.title, datos.body)
        return {"nota": nota}

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        print(f"Error al crear nota: {error}")
        raise HTTPException(
            status_code=500,
            detail="No se pudo crear la nota.",
        )


@app.patch("/notas/{nota_id}")
def modificar_nota(
    nota_id: str,
    datos: ActualizarNota,
    authorization: str | None = Header(default=None),
):
    uid = obtener_uid(authorization)

    try:
        actualizar_nota(
            uid,
            nota_id,
            titulo=datos.title,
            contenido=datos.body,
        )

        return {"mensaje": "Nota actualizada."}

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except Exception as error:
        print(f"Error al actualizar nota: {error}")
        raise HTTPException(
            status_code=500,
            detail="No se pudo actualizar la nota.",
        )


@app.delete("/notas/{nota_id}")
def borrar_nota(
    nota_id: str,
    authorization: str | None = Header(default=None),
):
    uid = obtener_uid(authorization)

    try:
        eliminar_nota(uid, nota_id)
        return {"mensaje": "Nota eliminada."}

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except Exception as error:
        print(f"Error al eliminar nota: {error}")
        raise HTTPException(
            status_code=500,
            detail="No se pudo eliminar la nota.",
        )
