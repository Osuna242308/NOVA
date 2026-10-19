
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.brain import procesar_comando

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

app = FastAPI(
    title="N.O.V.A.",
    description="Neural Operations & Virtual Assistant",
    version="1.1.0",
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
        "mensaje": "NOVA funciona, pero falta static/index.html.",
    }


@app.get("/health")
def salud():
    return {"estado": "ok"}


@app.post("/chat")
def chat(datos: Mensaje):
    if not datos.mensaje.strip():
        raise HTTPException(
            status_code=400,
            detail="El mensaje no puede estar vacío.",
        )

    try:
        respuesta = procesar_comando(datos.mensaje)
        return {"respuesta": str(respuesta)}
    except Exception as error:
        # El detalle técnico se conserva en los registros del servidor.
        print(f"Error al procesar el mensaje: {error}")
        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudo procesar el mensaje. "
                "Revisa los registros del servidor."
            ),
        ) from error
