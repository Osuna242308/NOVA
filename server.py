
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.brain import procesar_comando

app = FastAPI(
    title="N.O.V.A.",
    description="Neural Operations & Virtual Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Mensaje(BaseModel):
    mensaje: str


@app.get("/")
def inicio():
    return {
        "nombre": "N.O.V.A.",
        "estado": "en linea",
        "mensaje": "NOVA está funcionando."
    }


@app.get("/health")
def salud():
    return {"estado": "ok"}


@app.post("/chat")
def chat(datos: Mensaje):
    if not datos.mensaje.strip():
        raise HTTPException(
            status_code=400,
            detail="El mensaje no puede estar vacío."
        )

    try:
        respuesta = procesar_comando(datos.mensaje)
        return {"respuesta": str(respuesta)}
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="No se pudo procesar el mensaje. Revisa los registros del servidor."
        ) from error