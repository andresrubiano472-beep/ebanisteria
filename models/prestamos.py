"""Modelo de datos para solicitudes y gestión de préstamos.

Estados de una solicitud (columna prestamos.estado_solicitud):
    Pendiente -> Aprobado -> Devuelto
              -> Rechazado
"""
from conexion import get_connection
from models.herramientas import esta_disponible


def asegurar_esquema():
    """Se ejecuta una sola vez al arrancar. Compatibilidad con la tabla prestamos del SQL original."""
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS total FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='prestamos' "
                "AND COLUMN_NAME='estado_solicitud'"
            )
            if not cursor.fetchone()['total']:
                cursor.execute(
                    "ALTER TABLE prestamos ADD COLUMN estado_solicitud VARCHAR(20) NOT NULL DEFAULT 'Aprobado'"
                )
        conexion.commit()
    finally:
        conexion.close()


class Prestamo:
    @staticmethod
    def solicitar(id_estudiante, id_herramienta):
        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT estado FROM usuarios WHERE id_usuario=%s", (id_estudiante,))
                usuario = cursor.fetchone()
                if not usuario or usuario['estado'] != 'activo':
                    return False, 'Tu cuenta no está activa.'
                cursor.execute(
                    "SELECT cantidad, estado, activo FROM herramientas WHERE id_herramienta=%s FOR UPDATE",
                    (id_herramienta,)
                )
                herramienta = cursor.fetchone()
                if (not herramienta or not herramienta['activo']
                        or not esta_disponible(herramienta['cantidad'], herramienta['estado'])):
                    return False, 'La herramienta no está disponible en este momento.'
                cursor.execute(
                    "SELECT id_prestamo FROM prestamos WHERE id_estudiantefk=%s AND id_herramientafk=%s "
                    "AND estado_solicitud IN ('Pendiente','Aprobado')",
                    (id_estudiante, id_herramienta)
                )
                if cursor.fetchone():
                    return False, 'Ya tienes una solicitud pendiente o un préstamo activo de esta herramienta.'
                cursor.execute(
                    "INSERT INTO prestamos (id_estudiantefk, id_herramientafk, fecha_entrega, estado_solicitud) "
                    "VALUES (%s,%s,CURDATE(),'Pendiente')",
                    (id_estudiante, id_herramienta)
                )
                conexion.commit()
                return True, 'Solicitud enviada. El administrador debe aprobarla.'
        except Exception as exc:
            conexion.rollback()
            return False, f'No se pudo registrar la solicitud: {exc}'
        finally:
            conexion.close()

    @staticmethod
    def listar_todos():
        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("""SELECT p.id_prestamo, p.fecha_entrega, p.fecha_devolucion, p.estado_solicitud,
                    u.NombreCompleto AS estudiante, u.documento, h.nombre AS herramienta
                    FROM prestamos p JOIN usuarios u ON u.id_usuario=p.id_estudiantefk
                    JOIN herramientas h ON h.id_herramienta=p.id_herramientafk
                    ORDER BY FIELD(p.estado_solicitud,'Pendiente','Aprobado','Devuelto','Rechazado'), p.id_prestamo DESC""")
                return cursor.fetchall()
        finally:
            conexion.close()

    @staticmethod
    def listar_estudiante(id_estudiante):
        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("""SELECT p.id_prestamo,p.fecha_entrega,p.fecha_devolucion,p.estado_solicitud,h.nombre AS herramienta
                    FROM prestamos p JOIN herramientas h ON h.id_herramienta=p.id_herramientafk
                    WHERE p.id_estudiantefk=%s ORDER BY p.id_prestamo DESC""", (id_estudiante,))
                return cursor.fetchall()
        finally:
            conexion.close()

    @staticmethod
    def resolver(id_prestamo, decision, id_admin=None):
        if decision not in ('Aprobado', 'Rechazado'):
            return False, 'Decisión no válida.'
        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT id_herramientafk, estado_solicitud FROM prestamos WHERE id_prestamo=%s FOR UPDATE", (id_prestamo,))
                prestamo = cursor.fetchone()
                if not prestamo or prestamo['estado_solicitud'] != 'Pendiente':
                    return False, 'La solicitud ya fue procesada o no existe.'
                if decision == 'Aprobado':
                    cursor.execute("SELECT cantidad FROM herramientas WHERE id_herramienta=%s AND activo=1 FOR UPDATE", (prestamo['id_herramientafk'],))
                    herramienta = cursor.fetchone()
                    if not herramienta or (herramienta['cantidad'] or 0) < 1:
                        return False, 'No hay unidades disponibles para aprobar esta solicitud.'
                    cursor.execute("UPDATE herramientas SET cantidad=cantidad-1 WHERE id_herramienta=%s", (prestamo['id_herramientafk'],))
                    cursor.execute("UPDATE prestamos SET id_docentefk=%s, estado_solicitud='Aprobado' WHERE id_prestamo=%s", (id_admin, id_prestamo))
                else:
                    cursor.execute("UPDATE prestamos SET estado_solicitud='Rechazado', id_docentefk=%s WHERE id_prestamo=%s", (id_admin, id_prestamo))
                conexion.commit()
                return True, f'Solicitud {decision.lower()} correctamente.'
        except Exception as exc:
            conexion.rollback()
            return False, f'No se pudo procesar la solicitud: {exc}'
        finally:
            conexion.close()

    @staticmethod
    def devolver(id_prestamo, id_admin=None):
        """Registra la devolución: guarda la fecha en la BD, marca 'Devuelto' y repone la unidad al inventario."""
        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT id_herramientafk, estado_solicitud FROM prestamos WHERE id_prestamo=%s FOR UPDATE", (id_prestamo,))
                prestamo = cursor.fetchone()
                if not prestamo or prestamo['estado_solicitud'] != 'Aprobado':
                    return False, 'Solo se pueden devolver préstamos aprobados que sigan activos.'
                cursor.execute(
                    "UPDATE prestamos SET estado_solicitud='Devuelto', fecha_devolucion=CURDATE() "
                    "WHERE id_prestamo=%s", (id_prestamo,))
                cursor.execute("UPDATE herramientas SET cantidad=cantidad+1 WHERE id_herramienta=%s", (prestamo['id_herramientafk'],))
                conexion.commit()
                return True, 'Devolución registrada. La unidad volvió al inventario.'
        except Exception as exc:
            conexion.rollback()
            return False, f'No se pudo registrar la devolución: {exc}'
        finally:
            conexion.close()
