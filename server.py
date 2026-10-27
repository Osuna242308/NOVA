
import os
from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.brain import procesar_comando

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"


def iniciar_firebase():
    if not firebase_admin._apps:
        ruta = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not ruta or not os.path.isfile(ruta):
            raise RuntimeError(
                "No se encontró el archivo de credenciales de Firebase."
            )

        credencial = credentials.Certificate(ruta)
        firebase_admin.initialize_app(credencial)


iniciar_firebase()

app = FastAPI(
    title="N.O.V.A.",
    description="Neural Operations & Virtual Assistant",
    version="1.2.0",
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


class Mensaje(BaseModel):
    mensaje: str


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


@app.post("/chat")
def chat(
    datos: Mensaje,
    authorization: str | None = Header(default=None),
):
    if not datos.mensaje.strip():
        raise HTTPException(
            status_code=400,
            detail="El mensaje no puede estar vacío.",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión para usar NOVA.",
        )

    token = authorization.split(" ", 1)[1].strip()

    try:
        usuario = auth.verify_id_token(token)
        uid = usuario["uid"]
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Tu sesión no es válida. Inicia sesión nuevamente.",
        )

    try:
        respuesta = procesar_comando(datos.mensaje, uid)
        return {"respuesta": str(respuesta)}
    except Exception:
        print("Error al procesar el mensaje de NOVA.")
        raise HTTPException(
            status_code=500,
            detail="No se pudo procesar el mensaje. Revisa los registros del servidor.",
        )
