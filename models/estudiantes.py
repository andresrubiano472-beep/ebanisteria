from conexion import get_connection

GRADOS = [
    ('sexto', 'Sexto'),
    ('septimo', 'Séptimo'),
    ('octavo', 'Octavo'),
    ('noveno', 'Noveno'),
    ('decimo', 'Décimo'),
    ('once', 'Once'),
]

_COLUMNAS = "id_usuario, documento, NombreCompleto, grado, email, estado"


def estudiante(busqueda=None):
    """Lista de estudiantes (activos e inactivos). Permite filtrar por nombre, documento o correo."""
    cone = get_connection()
    try:
        with cone.cursor() as cursor:
            sql = f"SELECT {_COLUMNAS} FROM usuarios WHERE rol='estudiante'"
            params = []
            if busqueda:
                sql += " AND (NombreCompleto LIKE %s OR documento LIKE %s OR email LIKE %s)"
                params = [f"%{busqueda}%"] * 3
            sql += " ORDER BY estado ASC, NombreCompleto ASC"
            cursor.execute(sql, params or None)
            return cursor.fetchall()
    finally:
        cone.close()


def obtener_estudiante(id_usuario):
    cone = get_connection()
    try:
        with cone.cursor() as cursor:
            cursor.execute(
                f"SELECT {_COLUMNAS} FROM usuarios WHERE id_usuario=%s AND rol='estudiante'",
                (id_usuario,)
            )
            return cursor.fetchone()
    finally:
        cone.close()


def actualizar_estudiante(id_usuario, nombre, grado, email, documento=None):
    """Actualiza los datos de un estudiante. El documento solo se cambia si se envía (admin)."""
    cone = get_connection()
    try:
        with cone.cursor() as cursor:
            if documento is None:
                cursor.execute(
                    "UPDATE usuarios SET NombreCompleto=%s, grado=%s, email=%s "
                    "WHERE id_usuario=%s AND rol='estudiante'",
                    (nombre, grado, email, id_usuario)
                )
            else:
                cursor.execute(
                    "UPDATE usuarios SET NombreCompleto=%s, grado=%s, email=%s, documento=%s "
                    "WHERE id_usuario=%s AND rol='estudiante'",
                    (nombre, grado, email, documento, id_usuario)
                )
        cone.commit()
        return True
    finally:
        cone.close()


def cambiar_estado_estudiante(id_usuario, estado):
    """'inactivo' = quitar al estudiante (se conserva su historial). 'activo' = reactivarlo."""
    if estado not in ('activo', 'inactivo'):
        return False, 'Estado no válido.'
    cone = get_connection()
    try:
        with cone.cursor() as cursor:
            if estado == 'inactivo':
                cursor.execute(
                    "SELECT COUNT(*) AS total FROM prestamos "
                    "WHERE id_estudiantefk=%s AND estado_solicitud IN ('Pendiente','Aprobado')",
                    (id_usuario,)
                )
                if cursor.fetchone()['total']:
                    return False, ('El estudiante tiene solicitudes pendientes o herramientas sin devolver. '
                                   'Resuélvelas en Préstamos antes de quitarlo.')
            cursor.execute(
                "UPDATE usuarios SET estado=%s WHERE id_usuario=%s AND rol='estudiante'",
                (estado, id_usuario)
            )
        cone.commit()
        if estado == 'inactivo':
            return True, 'Estudiante quitado. Ya no podrá iniciar sesión (su historial se conserva).'
        return True, 'Estudiante reactivado correctamente.'
    finally:
        cone.close()
