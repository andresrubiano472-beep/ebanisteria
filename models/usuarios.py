import hmac

from werkzeug.security import generate_password_hash, check_password_hash

from conexion import get_connection  # Importa de conexion.py la funcion get_connection


def buscar_usuario(usuario):  # Busca un usuario por su correo
    cone = get_connection()
    try:
        with cone.cursor() as cursor:
            cursor.execute(
                "SELECT id_usuario,NombreCompleto,contraseña,rol,estado FROM usuarios WHERE email=%s",
                (usuario,)
            )
            return cursor.fetchone()
    finally:
        cone.close()


# ----------------------------------------------------------
# CONTRASEÑAS
# ----------------------------------------------------------
# Las cuentas antiguas guardan la contraseña en texto plano (ej. "12").
# Se siguen aceptando y se convierten a hash en el primer inicio de sesión.

def _es_hash(valor):
    return isinstance(valor, str) and valor.startswith(('scrypt:', 'pbkdf2:'))


def verificar_password(guardada, ingresada):
    if not guardada:
        return False
    if _es_hash(guardada):
        return check_password_hash(guardada, ingresada)
    return hmac.compare_digest(str(guardada), str(ingresada))


def necesita_actualizar_hash(guardada):
    return not _es_hash(guardada)


def actualizar_password(id_usuario, nueva):
    cone = get_connection()
    try:
        with cone.cursor() as cursor:
            cursor.execute(
                "UPDATE usuarios SET contraseña=%s WHERE id_usuario=%s",
                (generate_password_hash(nueva), id_usuario)
            )
        cone.commit()
        return True
    finally:
        cone.close()


# ----------------------------------------------------------
# REGISTRO
# ----------------------------------------------------------

def existe_usuario(email=None, documento=None, excluir_id=None):
    """Devuelve 'email' o 'documento' si ya los usa otro usuario; None si están libres."""
    cone = get_connection()
    try:
        with cone.cursor() as cursor:
            if email:
                cursor.execute(
                    "SELECT id_usuario FROM usuarios WHERE email=%s AND id_usuario<>%s",
                    (email, excluir_id or 0)
                )
                if cursor.fetchone():
                    return 'email'
            if documento:
                cursor.execute(
                    "SELECT id_usuario FROM usuarios WHERE documento=%s AND id_usuario<>%s",
                    (documento, excluir_id or 0)
                )
                if cursor.fetchone():
                    return 'documento'
        return None
    finally:
        cone.close()


def registro(datos):
    # datos = [documento, nombre, grado, email, password]
    datos = list(datos)
    datos[4] = generate_password_hash(datos[4])
    cone = get_connection()
    try:
        with cone.cursor() as cursor:
            cursor.callproc("registrarusuario", tuple(datos))
        cone.commit()
        return True
    finally:
        cone.close()
