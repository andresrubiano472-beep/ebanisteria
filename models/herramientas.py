from conexion import get_connection


def esta_disponible(cantidad, estado):
    """Misma regla que usa el panel del estudiante: hay unidades y la herramienta no está dañada."""
    return bool(cantidad and cantidad > 0 and (estado or '').lower() not in ('dañado', 'danado'))


ESTADOS_VALIDOS = ('Disponible', 'Prestado', 'Dañado')


def validar_herramienta(nombre, estado, cantidad, tipo):
    """Devuelve (mensaje_error, cantidad_entera). mensaje_error es None si todo está bien."""
    if not (nombre or '').strip() or not (tipo or '').strip():
        return 'El nombre y el tipo son obligatorios.', None
    if estado not in ESTADOS_VALIDOS:
        return 'El estado seleccionado no es válido.', None
    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        return 'La cantidad debe ser un número entero.', None
    if cantidad < 0:
        return 'La cantidad no puede ser negativa.', None
    return None, cantidad


class ConexionBD:
    @staticmethod
    def obtener_conexion():
        return get_connection()
 
class Herramienta:
   
    @staticmethod
    def obtener_todas():
        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            cursor.execute(
                "SELECT id_herramienta, nombre, tipo, cantidad, estado, descripcion FROM herramientas WHERE activo = 1 ORDER BY id_herramienta ASC"
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener herramientas: {e}")
            return []
        finally:
            conexion.close()
   
    @staticmethod
    def buscar(texto=None, solo_disponibles=False):
        """Búsqueda de herramientas por nombre, tipo o descripción (usada en la consulta pública)."""
        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = ("SELECT id_herramienta, nombre, tipo, cantidad, estado, descripcion "
                   "FROM herramientas WHERE activo = 1")
            params = []
            if texto:
                sql += " AND (nombre LIKE %s OR tipo LIKE %s OR descripcion LIKE %s)"
                params = [f"%{texto}%"] * 3
            sql += " ORDER BY nombre ASC"
            cursor.execute(sql, params or None)
            filas = cursor.fetchall()
            for fila in filas:
                fila['disponible'] = esta_disponible(fila['cantidad'], fila['estado'])
            if solo_disponibles:
                filas = [f for f in filas if f['disponible']]
            return filas
        except Exception as e:
            print(f"Error al buscar herramientas: {e}")
            return []
        finally:
            conexion.close()

    @staticmethod
    def obtener_por_id(id_herramienta):
        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = "SELECT id_herramienta, nombre, estado, cantidad, tipo, descripcion FROM herramientas WHERE id_herramienta = %s AND activo = 1"
            cursor.execute(sql, (id_herramienta,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener herramienta: {e}")
            return None
        finally:
            conexion.close()
   
    @staticmethod
    # SE CORRIGIÓ: Se invirtió el orden de cantidad y tipo para coincidir con app.py
    def crear(nombre, estado, cantidad, tipo, descripcion):
        error, cantidad = validar_herramienta(nombre, estado, cantidad, tipo)
        if error:
            return False, error
        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = "INSERT INTO herramientas (nombre, estado, cantidad, tipo, descripcion) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (nombre, estado, cantidad, tipo, descripcion))
            conexion.commit()
            return True, "Herramienta agregada exitosamente"
        except Exception as e:
            print(f"Error al agregar herramienta: {e}")
            return False, f"Error al agregar herramienta: {e}"
        finally:
            conexion.close()
   
    @staticmethod
    # SE CORRIGIÓ: Se ordenaron los parámetros igual que en app.py
    def actualizar(id_herramienta, nombre, estado, cantidad, tipo, descripcion):
        error, cantidad = validar_herramienta(nombre, estado, cantidad, tipo)
        if error:
            return False, error
        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE herramientas SET nombre = %s, estado = %s, cantidad = %s, tipo = %s, descripcion = %s WHERE id_herramienta = %s"
            cursor.execute(sql, (nombre, estado, cantidad, tipo, descripcion, id_herramienta))
            conexion.commit()
            return True, "Herramienta actualizada exitosamente"
        except Exception as e:
            print(f"Error al actualizar herramienta: {e}")
            return False, f"Error al actualizar herramienta: {e}"
        finally:
            conexion.close()
   
    @staticmethod
    def eliminar(id_herramienta):
        conexion = ConexionBD.obtener_conexion()
        try:
            cursor = conexion.cursor()
            sql = "UPDATE herramientas SET activo = 0 WHERE id_herramienta = %s"
            cursor.execute(sql, (id_herramienta,))
            conexion.commit()
            return True, "Herramienta eliminada exitosamente"
        except Exception as e:
            print(f"Error al eliminar herramienta: {e}")
            return False, f"Error al eliminar herramienta: {e}"
        finally:
            conexion.close()
