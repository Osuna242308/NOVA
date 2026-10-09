
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.brain import procesar_comando

app = FastAPI(title="NOVA API")

# Permite que la web de NOVA se comunique con este servidor.
# Después cambiaremos esto por el dominio exacto de Vercel.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class Mensaje(BaseModel):
    mensaje: str


@app.get("/")
def inicio():
    return {"estado": "NOVA API funcionando"}


@app.post("/chat")
def chat(datos: Mensaje):
    texto = datos.mensaje.strip()

    if not texto:
        raise HTTPException(
            status_code=400,
            detail="El mensaje no puede estar vacío."
        )

    try:
        respuesta = procesar_comando(texto)
        return {"respuesta": respuesta}

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="NOVA tuvo un problema al procesar el mensaje."
        )

