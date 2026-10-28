
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
    version="1.3.0",
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

    # Si es una conversación nueva, asignar un identificador.
    chat_id = datos.chat_id or str(uuid.uuid4())

    try:
        respuesta = procesar_comando(
            datos.mensaje,
            uid,
            chat_id,
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
# LISTAR CONVERSACIONES DEL USUARIO
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


# =========================================================
# RECUPERAR MENSAJES DE UNA CONVERSACIÓN
# =========================================================

@app.get("/chats/{chat_id}/mensajes")
def listar_mensajes(
    chat_id: str,
    authorization: str | None = Header(default=None),
):
    uid = obtener_uid(authorization)

    try:
        mensajes = obtener_mensajes_chat(
            uid,
            chat_id,
        )

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
