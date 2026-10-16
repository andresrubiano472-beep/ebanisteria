import os
import hmac
import secrets

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)
from markupsafe import Markup

from controllers.auth_controller import auth, requiere_rol
from controllers.estudiante_controller import (
    mostrarestudiante, editar_estudiante_admin, actualizar_estudiante_admin, estado_estudiante_admin,
    perfil_estudiante as _perfil_estudiante, actualizar_perfil_estudiante as _actualizar_perfil,
    cambiar_password_estudiante as _cambiar_password,
)
from controllers.prestamo_controller import prestamos_bp
from controllers.reportes_controller import reportes_bp
from models.herramientas import Herramienta
from models import prestamos as modelo_prestamos
from models import reportes as modelo_reportes


# ==========================================================
# CONFIGURACIÓN DE FLASK
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'Static'),
    static_url_path='/static'
)

# Puedes definir la variable de entorno ASSETMATE_SECRET_KEY en producción.
app.secret_key = os.environ.get("ASSETMATE_SECRET_KEY", "sistema12")

app.register_blueprint(auth)
app.register_blueprint(prestamos_bp)
app.register_blueprint(reportes_bp)


# ==========================================================
# SEGURIDAD: protección CSRF para todos los formularios POST
# ==========================================================

@app.context_processor
def _inyectar_csrf():
    if '_csrf' not in session:
        session['_csrf'] = secrets.token_hex(16)
    return {'csrf_input': Markup(f'<input type="hidden" name="_csrf" value="{session["_csrf"]}">')}


@app.before_request
def _verificar_csrf():
    if request.method == 'POST':
        enviado = request.form.get('_csrf', '')
        esperado = session.get('_csrf', '')
        if not esperado or not hmac.compare_digest(enviado, esperado):
            flash('La sesión del formulario expiró. Inténtalo de nuevo.')
            return redirect(request.referrer or url_for('index'))


# ==========================================================
# BASE DE DATOS: columnas/tablas necesarias (se revisan al arrancar)
# ==========================================================

def preparar_base_de_datos():
    try:
        modelo_prestamos.asegurar_esquema()
        modelo_reportes.asegurar_esquema()
    except Exception as exc:
        print(f"[AssetMate] No se pudo preparar la base de datos: {exc}")


# ==========================================================
# RUTAS PÚBLICAS
# ==========================================================

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/Login')
def Login():
    return render_template('Login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión")
    return redirect(url_for("index"))


# ==========================================================
# DASHBOARD ADMINISTRADOR
# ==========================================================

@app.route('/home')
@app.route('/dashboard')
@requiere_rol('admin')
def dashboard():
    return render_template('dashboard/home.html')


# ==========================================================
# ESTUDIANTES (administrador)
# ==========================================================

@app.route('/estudiantes')
@requiere_rol('admin')
def ver_estudiantes():
    return mostrarestudiante()


@app.route('/estudiantes/<int:id_usuario>/editar')
@requiere_rol('admin')
def editar_estudiante(id_usuario):
    return editar_estudiante_admin(id_usuario)


@app.route('/estudiantes/<int:id_usuario>/actualizar', methods=['POST'])
@requiere_rol('admin')
def actualizar_estudiante(id_usuario):
    return actualizar_estudiante_admin(id_usuario)


@app.route('/estudiantes/<int:id_usuario>/estado', methods=['POST'])
@requiere_rol('admin')
def estado_estudiante(id_usuario):
    return estado_estudiante_admin(id_usuario)


# ==========================================================
# HERRAMIENTAS (administrador)
# ==========================================================

@app.route('/herramientas')
@app.route('/dashboard/pages/herramientas')
@app.route('/ver_herramientas')
@requiere_rol('admin')
def mostrar_herramientas_dashboard():
    herramientas = Herramienta.obtener_todas()
    return render_template(
        'dashboard/pages/herramientas.html',
        herramientas=herramientas,
        total_registros=len(herramientas)
    )


@app.route('/agregar_herramienta', methods=['POST'])
@requiere_rol('admin')
def agregar_herramienta():
    exito, mensaje = Herramienta.crear(
        request.form.get('nombre'),
        request.form.get('estado'),
        request.form.get('cantidad'),
        request.form.get('tipo'),
        request.form.get('descripcion')
    )
    flash(mensaje)
    return redirect(url_for('mostrar_herramientas_dashboard'))


@app.route('/eliminar_herramienta/<id_herramienta>', methods=['POST'])
@requiere_rol('admin')
def eliminar_herramienta(id_herramienta):
    exito, mensaje = Herramienta.eliminar(id_herramienta)
    flash(mensaje)
    return redirect(url_for('mostrar_herramientas_dashboard'))


@app.route('/editar_herramienta/<id_herramienta>')
@requiere_rol('admin')
def editar_herramienta(id_herramienta):
    herramienta = Herramienta.obtener_por_id(id_herramienta)
    if not herramienta:
        flash('La herramienta no existe.')
        return redirect(url_for('mostrar_herramientas_dashboard'))
    return render_template('dashboard/pages/editar_herramienta.html', herramienta=herramienta)


@app.route('/actualizar_herramienta', methods=['POST'])
@requiere_rol('admin')
def actualizar_herramienta():
    exito, mensaje = Herramienta.actualizar(
        request.form.get('id'),
        request.form.get('nombre'),
        request.form.get('estado'),
        request.form.get('cantidad'),
        request.form.get('tipo'),
        request.form.get('descripcion')
    )
    flash(mensaje)
    return redirect(url_for('mostrar_herramientas_dashboard'))


# ==========================================================
# PANEL ESTUDIANTE
# (préstamos y herramientas del estudiante están en prestamo_controller.py)
# ==========================================================

@app.route('/estudiantehome')
@app.route('/home_estudiantes')
@requiere_rol('estudiante')
def dashboardest():
    return render_template('dashboard_estudiantes/home_estudiantes.html')


@app.route('/perfil')
@requiere_rol('estudiante')
def perfil_estudiante():
    return _perfil_estudiante()


@app.route('/perfil/actualizar', methods=['POST'])
@requiere_rol('estudiante')
def actualizar_perfil_estudiante():
    return _actualizar_perfil()


@app.route('/perfil/password', methods=['POST'])
@requiere_rol('estudiante')
def cambiar_password_estudiante():
    return _cambiar_password()


preparar_base_de_datos()

if __name__ == "__main__":
    app.run(debug=True)
