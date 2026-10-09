import os
import firebase_admin

from firebase_admin import credentials
from firebase_admin import firestore


# =========================================================
# CONEXIÓN CON FIREBASE
# =========================================================

def conectar_firebase():

    if not firebase_admin._apps:

        ruta_credenciales = os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )

        if not ruta_credenciales:
            raise Exception(
                "No se encontró GOOGLE_APPLICATION_CREDENTIALS."
            )

        credencial = credentials.Certificate(
            ruta_credenciales
        )

        firebase_admin.initialize_app(
            credencial
        )

    return firestore.client()


# =========================================================
# INICIAR MEMORIA
# =========================================================

def crear_memoria():

    db = conectar_firebase()

    # Crear la colección solamente cuando
    # se guarde el primer recuerdo.
    return db


# =========================================================
# GUARDAR RECUERDO
# =========================================================

def guardar_recuerdo(clave, valor):

    db = conectar_firebase()

    referencia = (
        db.collection("recuerdos")
        .document(clave)
    )

    referencia.set({
        "clave": clave,
        "valor": valor
    })


# =========================================================
# BUSCAR RECUERDO
# =========================================================

def buscar_recuerdo(clave):

    db = conectar_firebase()

    referencia = (
        db.collection("recuerdos")
        .document(clave)
    )

    documento = referencia.get()

    if documento.exists:

        datos = documento.to_dict()

        return datos.get("valor")

    return None


# =========================================================
# OBTENER TODOS LOS RECUERDOS
# =========================================================

def obtener_recuerdos():

    db = conectar_firebase()

    documentos = (
        db.collection("recuerdos")
        .stream()
    )

    recuerdos = []

    for documento in documentos:

        datos = documento.to_dict()

        clave = datos.get(
            "clave",
            documento.id
        )

        valor = datos.get(
            "valor",
            ""
        )

        recuerdos.append(
            (clave, valor)
        )

    return recuerdos


# =========================================================
# OLVIDAR RECUERDO
# =========================================================

def olvidar_recuerdo(clave):

    db = conectar_firebase()

    referencia = (
        db.collection("recuerdos")
        .document(clave)
    )

    referencia.delete()