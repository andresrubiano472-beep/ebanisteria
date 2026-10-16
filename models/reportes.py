from datetime import date

from conexion import get_connection

ESTADOS = ('Pendiente', 'Aprobado', 'Devuelto', 'Rechazado')


def asegurar_esquema():
    """Crea la tabla donde queda registrado cada reporte generado (solo si no existe)."""
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""CREATE TABLE IF NOT EXISTS reportes (
                id_reporte INT AUTO_INCREMENT PRIMARY KEY,
                fecha_generacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_desde DATE NOT NULL,
                fecha_hasta DATE NOT NULL,
                id_adminfk INT NULL,
                total_solicitudes INT NOT NULL DEFAULT 0,
                total_aprobadas INT NOT NULL DEFAULT 0,
                total_devueltas INT NOT NULL DEFAULT 0,
                total_rechazadas INT NOT NULL DEFAULT 0,
                total_pendientes INT NOT NULL DEFAULT 0,
                FOREIGN KEY (id_adminfk) REFERENCES usuarios(id_usuario)
            )""")
        conexion.commit()
    finally:
        conexion.close()


# Un préstamo pertenece al periodo si se solicitó o se devolvió dentro de él.
_FILTRO_FECHAS = "(p.fecha_entrega BETWEEN %s AND %s OR p.fecha_devolucion BETWEEN %s AND %s)"


class Reporte:
    @staticmethod
    def resumen(desde=None, hasta=None):
        """Resumen de movimientos entre dos fechas (por defecto: del 1 del mes actual a hoy)."""
        hoy = date.today()
        desde = desde or hoy.replace(day=1)
        hasta = hasta or hoy
        rango = (desde, hasta, desde, hasta)

        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS total FROM herramientas WHERE activo=1")
                herramientas = cursor.fetchone()['total']
                cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol='estudiante' AND estado='activo'")
                estudiantes = cursor.fetchone()['total']

                cursor.execute(
                    f"SELECT p.estado_solicitud, COUNT(*) AS total FROM prestamos p WHERE {_FILTRO_FECHAS} "
                    "GROUP BY p.estado_solicitud", rango)
                conteo = {f['estado_solicitud']: f['total'] for f in cursor.fetchall()}
                estados = [{'estado_solicitud': e, 'total': conteo.get(e, 0)} for e in ESTADOS]
                prestamos = sum(conteo.values())

                cursor.execute(f"""SELECT h.nombre AS herramienta, COUNT(p.id_prestamo) AS solicitudes,
                    SUM(CASE WHEN p.estado_solicitud IN ('Aprobado','Devuelto') THEN 1 ELSE 0 END) AS aprobados
                    FROM herramientas h LEFT JOIN prestamos p ON p.id_herramientafk=h.id_herramienta
                    AND {_FILTRO_FECHAS}
                    WHERE h.activo=1
                    GROUP BY h.id_herramienta,h.nombre ORDER BY solicitudes DESC,h.nombre""", rango)
                por_herramienta = cursor.fetchall()

                cursor.execute(f"""SELECT p.id_prestamo,u.NombreCompleto AS estudiante,h.nombre AS herramienta,
                    p.fecha_entrega,p.fecha_devolucion,p.estado_solicitud FROM prestamos p
                    JOIN usuarios u ON u.id_usuario=p.id_estudiantefk
                    JOIN herramientas h ON h.id_herramienta=p.id_herramientafk
                    WHERE {_FILTRO_FECHAS}
                    ORDER BY p.fecha_entrega DESC, p.id_prestamo DESC LIMIT 500""", rango)
                recientes = cursor.fetchall()

                return {'desde': desde, 'hasta': hasta,
                        'herramientas': herramientas, 'estudiantes': estudiantes, 'prestamos': prestamos,
                        'conteo': conteo, 'estados': estados,
                        'por_herramienta': por_herramienta, 'recientes': recientes}
        finally:
            conexion.close()

    @staticmethod
    def registrar(datos, id_admin):
        """Guarda en la base de datos que se generó un reporte (fechas, quién lo generó y totales)."""
        c = datos['conteo']
        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO reportes (fecha_desde, fecha_hasta, id_adminfk, total_solicitudes, "
                    "total_aprobadas, total_devueltas, total_rechazadas, total_pendientes) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (datos['desde'], datos['hasta'], id_admin, datos['prestamos'],
                     c.get('Aprobado', 0), c.get('Devuelto', 0), c.get('Rechazado', 0), c.get('Pendiente', 0)))
                id_reporte = cursor.lastrowid
            conexion.commit()
            return id_reporte
        finally:
            conexion.close()

    @staticmethod
    def historial(limite=15):
        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT r.*, u.NombreCompleto AS admin FROM reportes r "
                    "LEFT JOIN usuarios u ON u.id_usuario=r.id_adminfk "
                    "ORDER BY r.id_reporte DESC LIMIT %s", (limite,))
                return cursor.fetchall()
        finally:
            conexion.close()

    @staticmethod
    def obtener(id_reporte):
        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT * FROM reportes WHERE id_reporte=%s", (id_reporte,))
                return cursor.fetchone()
        finally:
            conexion.close()
