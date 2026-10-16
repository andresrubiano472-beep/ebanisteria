from flask import render_template, url_for, redirect, request, flash, session

from models.estudiantes import (
    estudiante, obtener_estudiante, actualizar_estudiante, cambiar_estado_estudiante, GRADOS,
)
from models.usuarios import existe_usuario, verificar_password, buscar_usuario, actualizar_password


def mostrarestudiante():
    busqueda = request.args.get('q', '').strip()
    estudiantess = estudiante(busqueda or None)
    return render_template('dashboard/pages/estudiantes.html', lista=estudiantess, busqueda=busqueda)


def _validar_datos(nombre, grado, email, id_usuario, documento=None):
    """Devuelve un mensaje de error o None si los datos son correctos."""
    if not nombre or not email or (documento is not None and not documento):
        return 'Completa todos los campos obligatorios.'
    if '@' not in email:
        return 'Escribe un correo válido.'
    if grado not in dict(GRADOS) and grado != '0000':
        return 'Selecciona un grado válido.'
    repetido = existe_usuario(email=email, documento=documento, excluir_id=id_usuario)
    if repetido == 'email':
        return 'Ese correo ya está en uso por otro usuario.'
    if repetido == 'documento':
        return 'Ese documento ya está registrado.'
    return None


# ----------------------------------------------------------
# ADMINISTRADOR: editar / quitar estudiantes
# ----------------------------------------------------------

def editar_estudiante_admin(id_usuario):
    alumno = obtener_estudiante(id_usuario)
    if not alumno:
        flash('El estudiante no existe.')
        return redirect(url_for('ver_estudiantes'))
    return render_template('dashboard/pages/estudiante_editar.html', alumno=alumno, grados=GRADOS)


def actualizar_estudiante_admin(id_usuario):
    if not obtener_estudiante(id_usuario):
        flash('El estudiante no existe.')
        return redirect(url_for('ver_estudiantes'))
    nombre = request.form.get('nombre', '').strip()
    grado = request.form.get('grado', '')
    email = request.form.get('email', '').strip()
    documento = request.form.get('documento', '').strip()
    error = _validar_datos(nombre, grado, email, id_usuario, documento)
    if error:
        flash(error)
        return redirect(url_for('editar_estudiante', id_usuario=id_usuario))
    actualizar_estudiante(id_usuario, nombre, grado, email, documento)
    flash('Datos del estudiante actualizados correctamente.')
    return redirect(url_for('ver_estudiantes'))


def estado_estudiante_admin(id_usuario):
    nuevo = 'activo' if request.form.get('accion') == 'reactivar' else 'inactivo'
    if not obtener_estudiante(id_usuario):
        flash('El estudiante no existe.')
    else:
        _, mensaje = cambiar_estado_estudiante(id_usuario, nuevo)
        flash(mensaje)
    return redirect(url_for('ver_estudiantes'))


# ----------------------------------------------------------
# ESTUDIANTE: editar sus propios datos
# ----------------------------------------------------------

def perfil_estudiante():
    alumno = obtener_estudiante(session['id_usuario'])
    return render_template('dashboard_estudiantes/perfil.html', alumno=alumno, grados=GRADOS)


def actualizar_perfil_estudiante():
    id_usuario = session['id_usuario']
    nombre = request.form.get('nombre', '').strip()
    grado = request.form.get('grado', '')
    email = request.form.get('email', '').strip()
    error = _validar_datos(nombre, grado, email, id_usuario)
    if error:
        flash(error)
        return redirect(url_for('perfil_estudiante'))
    actualizar_estudiante(id_usuario, nombre, grado, email)  # el documento solo lo cambia el administrador
    session['usuario'] = email
    session['nombre'] = nombre
    flash('Tus datos se actualizaron correctamente.')
    return redirect(url_for('perfil_estudiante'))


def cambiar_password_estudiante():
    actual = request.form.get('actual', '')
    nueva = request.form.get('nueva', '')
    confirmar = request.form.get('confirmar', '')
    alumno = obtener_estudiante(session['id_usuario'])
    usuariodb = buscar_usuario(alumno['email']) if alumno else None
    if not usuariodb or not verificar_password(usuariodb['contraseña'], actual):
        flash('La contraseña actual no es correcta.')
    elif len(nueva) < 4:
        flash('La nueva contraseña debe tener al menos 4 caracteres.')
    elif nueva != confirmar:
        flash('La confirmación no coincide con la nueva contraseña.')
    else:
        actualizar_password(session['id_usuario'], nueva)
        flash('Contraseña actualizada correctamente.')
    return redirect(url_for('perfil_estudiante'))
