
import os
import firebase_admin

from firebase_admin import credentials
from firebase_admin import firestore


def conectar_firebase():
    if not firebase_admin._apps:
        ruta_credenciales = os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )

        if not ruta_credenciales:
            raise RuntimeError(
                "No se encontró GOOGLE_APPLICATION_CREDENTIALS."
            )

        credencial = credentials.Certificate(ruta_credenciales)
        firebase_admin.initialize_app(credencial)

    return firestore.client()


def crear_memoria():
    return conectar_firebase()


def guardar_recuerdo(uid, clave, valor):
    db = conectar_firebase()

    referencia = (
        db.collection("usuarios")
        .document(uid)
        .collection("recuerdos")
        .document(clave)
    )

    referencia.set({
        "clave": clave,
        "valor": valor
    })


def buscar_recuerdo(uid, clave):
    db = conectar_firebase()

    documento = (
        db.collection("usuarios")
        .document(uid)
        .collection("recuerdos")
        .document(clave)
        .get()
    )

    if documento.exists:
        return documento.to_dict().get("valor")

    return None


def obtener_recuerdos(uid):
    db = conectar_firebase()

    documentos = (
        db.collection("usuarios")
        .document(uid)
        .collection("recuerdos")
        .stream()
    )

    recuerdos = []

    for documento in documentos:
        datos = documento.to_dict()

        clave = datos.get("clave", documento.id)
        valor = datos.get("valor", "")

        recuerdos.append((clave, valor))

    return recuerdos


def olvidar_recuerdo(uid, clave):
    db = conectar_firebase()

    (
        db.collection("usuarios")
        .document(uid)
        .collection("recuerdos")
        .document(clave)
        .delete()
    )
