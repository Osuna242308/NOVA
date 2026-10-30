
import os
import uuid

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

    referencia = (
        conectar_firebase()
        .collection("usuarios")
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
# TAREAS DEL USUARIO
# =========================================================

def obtener_tareas(uid):
    if not uid:
        raise ValueError("Se requiere el UID del usuario.")

    documentos = (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("tareas")
        .stream()
    )

    tareas = []

    for documento in documentos:
        datos = documento.to_dict() or {}

        tareas.append({
            "id": documento.id,
            "text": datos.get("text", ""),
            "done": datos.get("done", False),
        })

    return tareas


def crear_tarea(uid, texto):
    if not uid:
        raise ValueError("Se requiere el UID del usuario.")

    texto = str(texto).strip()

    if not texto:
        raise ValueError("La tarea no puede estar vacía.")

    tarea_id = str(uuid.uuid4())

    (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("tareas")
        .document(tarea_id)
        .set({
            "text": texto,
            "done": False,
            "creada": firestore.SERVER_TIMESTAMP,
        })
    )

    return {
        "id": tarea_id,
        "text": texto,
        "done": False,
    }


def actualizar_tarea(uid, tarea_id, texto=None, done=None):
    if not uid or not tarea_id:
        raise ValueError("Se requiere el UID y el ID de la tarea.")

    cambios = {}

    if texto is not None:
        texto = str(texto).strip()

        if not texto:
            raise ValueError("El texto de la tarea no puede estar vacío.")

        cambios["text"] = texto

    if done is not None:
        cambios["done"] = bool(done)

    if not cambios:
        return

    referencia = (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("tareas")
        .document(tarea_id)
    )

    if not referencia.get().exists:
        raise ValueError("La tarea no existe.")

    referencia.update(cambios)


def eliminar_tarea(uid, tarea_id):
    if not uid or not tarea_id:
        raise ValueError("Se requiere el UID y el ID de la tarea.")

    referencia = (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("tareas")
        .document(tarea_id)
    )

    if not referencia.get().exists:
        raise ValueError("La tarea no existe.")

    referencia.delete()


# =========================================================
# NOTAS DEL USUARIO
# =========================================================

def obtener_notas(uid):
    if not uid:
        raise ValueError("Se requiere el UID del usuario.")

    documentos = (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("notas")
        .stream()
    )

    notas = []

    for documento in documentos:
        datos = documento.to_dict() or {}

        notas.append({
            "id": documento.id,
            "title": datos.get("title", ""),
            "body": datos.get("body", ""),
        })

    return notas


def crear_nota(uid, titulo, contenido):
    if not uid:
        raise ValueError("Se requiere el UID del usuario.")

    titulo = str(titulo).strip()
    contenido = str(contenido).strip()

    if not titulo and not contenido:
        raise ValueError("La nota no puede estar vacía.")

    nota_id = str(uuid.uuid4())

    (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("notas")
        .document(nota_id)
        .set({
            "title": titulo,
            "body": contenido,
            "creada": firestore.SERVER_TIMESTAMP,
        })
    )

    return {
        "id": nota_id,
        "title": titulo,
        "body": contenido,
    }


def actualizar_nota(uid, nota_id, titulo=None, contenido=None):
    if not uid or not nota_id:
        raise ValueError("Se requiere el UID y el ID de la nota.")

    cambios = {}

    if titulo is not None:
        cambios["title"] = str(titulo).strip()

    if contenido is not None:
        cambios["body"] = str(contenido).strip()

    if not cambios:
        return

    referencia = (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("notas")
        .document(nota_id)
    )

    if not referencia.get().exists:
        raise ValueError("La nota no existe.")

    cambios["actualizada"] = firestore.SERVER_TIMESTAMP
    referencia.update(cambios)


def eliminar_nota(uid, nota_id):
    if not uid or not nota_id:
        raise ValueError("Se requiere el UID y el ID de la nota.")

    referencia = (
        conectar_firebase()
        .collection("usuarios")
        .document(uid)
        .collection("notas")
        .document(nota_id)
    )

    if not referencia.get().exists:
        raise ValueError("La nota no existe.")

    referencia.delete()


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
