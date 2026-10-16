from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.prestamos import Prestamo
from models.herramientas import Herramienta, esta_disponible
from controllers.auth_controller import requiere_rol

prestamos_bp = Blueprint('prestamos_modulo', __name__)


@prestamos_bp.route('/prestamos')
@requiere_rol('admin')
def administrar_prestamos():
    return render_template('dashboard/pages/prestamos.html', prestamos=Prestamo.listar_todos())


@prestamos_bp.route('/solicitar_prestamo', methods=['POST'])
@requiere_rol('estudiante')
def solicitar_prestamo():
    ok, mensaje = Prestamo.solicitar(session['id_usuario'], request.form.get('id_herramienta'))
    flash(mensaje)
    return redirect(url_for('prestamos_modulo.ver_herramientas_estudiantes'))


@prestamos_bp.route('/resolver_prestamo/<int:id_prestamo>', methods=['POST'])
@requiere_rol('admin')
def resolver_prestamo(id_prestamo):
    ok, mensaje = Prestamo.resolver(id_prestamo, request.form.get('decision'), session.get('id_usuario'))
    flash(mensaje)
    return redirect(url_for('prestamos_modulo.administrar_prestamos'))


@prestamos_bp.route('/devolver_prestamo/<int:id_prestamo>', methods=['POST'])
@requiere_rol('admin')
def devolver_prestamo(id_prestamo):
    ok, mensaje = Prestamo.devolver(id_prestamo, session.get('id_usuario'))
    flash(mensaje)
    return redirect(url_for('prestamos_modulo.administrar_prestamos'))


@prestamos_bp.route('/ver_prestamos')
@requiere_rol('estudiante')
def ver_prestamos_estudiante():
    return render_template('dashboard_estudiantes/ver_prestamos.html', prestamos=Prestamo.listar_estudiante(session['id_usuario']))


@prestamos_bp.route('/ver_herramientas_estudiantes')
@requiere_rol('estudiante')
def ver_herramientas_estudiantes():
    herramientas = Herramienta.obtener_todas()
    for h in herramientas:
        h['disponible'] = esta_disponible(h['cantidad'], h['estado'])
    return render_template('dashboard_estudiantes/herramientas_estudiantes.html', herramientas=herramientas)


# ----------------------------------------------------------
# CONSULTA PÚBLICA DE DISPONIBILIDAD (sin iniciar sesión)
# Usa la misma regla de disponibilidad que el panel del estudiante.
# ----------------------------------------------------------

@prestamos_bp.route('/disponibilidad')
def disponibilidad():
    texto = request.args.get('q', '').strip()
    solo_disponibles = request.args.get('solo_disponibles') == '1'
    herramientas = Herramienta.buscar(texto or None, solo_disponibles)
    return render_template('disponibilidad.html', herramientas=herramientas,
                           q=texto, solo_disponibles=solo_disponibles)
