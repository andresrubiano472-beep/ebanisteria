from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from models.usuarios import (
    buscar_usuario, registro, verificar_password, necesita_actualizar_hash,
    actualizar_password, existe_usuario,
)
from models.estudiantes import GRADOS

auth = Blueprint('auth', __name__)


def requiere_rol(rol):
    """Protege una ruta: solo entra quien haya iniciado sesión con ese rol."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if session.get('rol') != rol or not session.get('id_usuario'):
                flash('Inicia sesión como administrador.' if rol == 'admin' else 'Inicia sesión como estudiante.')
                return redirect(url_for('Login'))
            return vista(*args, **kwargs)
        return envoltura
    return decorador


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('Login.html')
    usuario = request.form.get('usuario', '').strip()
    password = request.form.get('contraseña', '')
    usuariodb = buscar_usuario(usuario)
    # Validación si el usuario buscado tiene la contraseña introducida
    if not usuariodb or not verificar_password(usuariodb['contraseña'], password):
        flash("Usuario o Contraseña incorrectos")
        return redirect(url_for('Login'))
    if usuariodb['estado'] != 'activo':
        flash("Tu cuenta está inactiva. Comunícate con el administrador.")
        return redirect(url_for('Login'))
    if necesita_actualizar_hash(usuariodb['contraseña']):
        actualizar_password(usuariodb['id_usuario'], password)  # guarda la contraseña cifrada
    session.clear()
    session["usuario"] = usuario
    session['id_usuario'] = usuariodb['id_usuario']
    session['rol'] = usuariodb['rol']
    session['nombre'] = usuariodb['NombreCompleto']
    if usuariodb['rol'] == "admin":
        return redirect(url_for('dashboard'))
    if usuariodb['rol'] == "estudiante":
        return redirect(url_for('dashboardest'))
    session.clear()
    flash("Tu rol no tiene acceso al sistema.")
    return redirect(url_for('Login'))


@auth.route('/Register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('Register.html', grados=GRADOS)
    documento = request.form.get('documentoidentidad', '').strip()
    nombre = request.form.get('nombreregistro', '').strip()
    grado = request.form.get('option-cursos')
    email = request.form.get('emailregistro', '').strip()
    password = request.form.get('passwordregistro', '')
    confirmar = request.form.get('confirmpassword', '')

    if not documento or not nombre or not email or not password:
        flash("Completa todos los campos.")
    elif grado not in dict(GRADOS):
        flash("Selecciona un grado válido.")
    elif password != confirmar:
        flash("Las contraseñas no coinciden.")
    elif len(password) < 4:
        flash("La contraseña debe tener al menos 4 caracteres.")
    else:
        repetido = existe_usuario(email=email, documento=documento)
        if repetido == 'email':
            flash("Ya existe una cuenta con ese correo.")
        elif repetido == 'documento':
            flash("Ya existe una cuenta con ese documento.")
        else:
            registro([documento, nombre, grado, email, password])
            flash("Usuario Registrado Correctamente")
            return redirect(url_for('auth.login'))
    return redirect(url_for('auth.register'))
