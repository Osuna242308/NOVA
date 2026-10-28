
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
    
# =========================================================
# HISTORIAL DE CONVERSACIONES
# =========================================================

def guardar_mensaje_chat(uid, chat_id, rol, contenido):
    if not uid:
        raise ValueError("Se requiere el UID del usuario.")

    if not chat_id:
        raise ValueError("Se requiere el ID de la conversación.")

    db = conectar_firebase()

    referencia_chat = (
        db.collection("usuarios")
        .document(uid)
        .collection("chats")
        .document(chat_id)
    )

    referencia_chat.set({
        "actualizado": firestore.SERVER_TIMESTAMP,
    }, merge=True)

    referencia_chat.collection("mensajes").add({
        "rol": rol,
        "contenido": contenido,
        "fecha": firestore.SERVER_TIMESTAMP,
    })


def obtener_chats(uid):
    if not uid:
        raise ValueError("Se requiere el UID del usuario.")

    db = conectar_firebase()

    documentos = (
        db.collection("usuarios")
        .document(uid)
        .collection("chats")
        .order_by("actualizado", direction=firestore.Query.DESCENDING)
        .stream()
    )

    chats = []

    for documento in documentos:
        datos = documento.to_dict()
        chats.append({
            "id": documento.id,
            "actualizado": datos.get("actualizado"),
        })

    return chats


def obtener_mensajes_chat(uid, chat_id):
    if not uid or not chat_id:
        raise ValueError("Falta el usuario o la conversación.")

    db = conectar_firebase()

    referencia = (
        db.collection("usuarios")
        .document(uid)
        .collection("chats")
        .document(chat_id)
    )

    # Verificar que la conversación exista dentro de la cuenta.
    if not referencia.get().exists:
        return []

    documentos = (
        referencia.collection("mensajes")
        .order_by("fecha")
        .stream()
    )

    return [
        {
            "rol": documento.to_dict().get("rol", ""),
            "contenido": documento.to_dict().get("contenido", ""),
        }
        for documento in documentos
    ]

