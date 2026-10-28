
import os

import firebase_admin
from firebase_admin import credentials, firestore


def conectar_firebase():
    if not firebase_admin._apps:
        ruta = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not ruta or not os.path.isfile(ruta):
            raise RuntimeError(
                "No se encontró un archivo válido en "
                "GOOGLE_APPLICATION_CREDENTIALS."
            )

        credencial = credentials.Certificate(ruta)
        firebase_admin.initialize_app(credencial)

    return firestore.client()


# =========================================================
# RECUERDOS DEL USUARIO
# =========================================================

def crear_memoria():
    return conectar_firebase()


def guardar_recuerdo(uid, clave, valor):
    if not uid:
        raise ValueError("Se requiere el UID del usuario.")

    db = conectar_firebase()

    referencia = (
        db.collection("usuarios")
        .document(uid)
        .collection("recuerdos")
        .document(clave)
    )

    referencia.set({
        "clave": clave,
        "valor": valor,
    })


def buscar_recuerdo(uid, clave):
    if not uid:
        raise ValueError("Se requiere el UID del usuario.")

    documento = (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("recuerdos")
        .document(clave)
        .get()
    )

    if documento.exists:
        return documento.to_dict().get("valor")

    return None


def obtener_recuerdos(uid):
    if not uid:
        raise ValueError("Se requiere el UID del usuario.")

    documentos = (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("recuerdos")
        .stream()
    )

    recuerdos = []

    for documento in documentos:
        datos = documento.to_dict() or {}

        recuerdos.append((
            datos.get("clave", documento.id),
            datos.get("valor", ""),
        ))

    return recuerdos


def olvidar_recuerdo(uid, clave):
    if not uid:
        raise ValueError("Se requiere el UID del usuario.")

    (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("recuerdos")
        .document(clave)
        .delete()
    )


# =========================================================
# HISTORIAL DE CONVERSACIONES
# =========================================================

def guardar_mensaje_chat(uid, chat_id, rol, contenido):
    if not uid or not chat_id:
        raise ValueError(
            "Se requiere el UID y el ID de la conversación."
        )

    if rol not in ("usuario", "nova"):
        raise ValueError("El rol del mensaje no es válido.")

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
        "contenido": str(contenido),
        "fecha": firestore.SERVER_TIMESTAMP,
    })


def obtener_chats(uid):
    if not uid:
        raise ValueError("Se requiere el UID del usuario.")

    documentos = (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("chats")
        .order_by(
            "actualizado",
            direction=firestore.Query.DESCENDING,
        )
        .stream()
    )

    chats = []

    for documento in documentos:
        datos = documento.to_dict() or {}
        fecha = datos.get("actualizado")

        chats.append({
            "id": documento.id,
            "actualizado": fecha.isoformat() if fecha else None,
        })

    return chats


def obtener_mensajes_chat(uid, chat_id):
    if not uid or not chat_id:
        raise ValueError(
            "Falta el usuario o la conversación."
        )

    referencia_chat = (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("chats")
        .document(chat_id)
    )

    # La conversación debe pertenecer a la cuenta indicada.
    if not referencia_chat.get().exists:
        return []

    documentos = (
        referencia_chat.collection("mensajes")
        .order_by("fecha")
        .stream()
    )

    mensajes = []

    for documento in documentos:
        datos = documento.to_dict() or {}

        mensajes.append({
            "rol": datos.get("rol", ""),
            "contenido": datos.get("contenido", ""),
        })

    return mensajes
