from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, session, request, Response

from models.reportes import Reporte
from models.pdf_reportes import generar_pdf
from controllers.auth_controller import requiere_rol

reportes_bp = Blueprint('reportes_modulo', __name__)


def _fecha(texto):
    try:
        return datetime.strptime(texto, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _rango_solicitado():
    """Lee ?desde=&hasta= (AAAA-MM-DD). Por defecto: del 1 del mes actual a hoy."""
    hoy = date.today()
    desde = _fecha(request.args.get('desde')) or hoy.replace(day=1)
    hasta = _fecha(request.args.get('hasta')) or hoy
    if desde > hasta:
        desde, hasta = hasta, desde
    return desde, hasta


@reportes_bp.route('/reportes')
@requiere_rol('admin')
def reportes():
    desde, hasta = _rango_solicitado()
    hoy = date.today()
    mes_anterior_fin = hoy.replace(day=1) - timedelta(days=1)
    return render_template(
        'dashboard/pages/reportes.html',
        reporte=Reporte.resumen(desde, hasta),
        historial=Reporte.historial(),
        mes_actual=(hoy.replace(day=1), hoy),
        mes_anterior=(mes_anterior_fin.replace(day=1), mes_anterior_fin),
    )


@reportes_bp.route('/reportes/pdf')
@requiere_rol('admin')
def reporte_pdf():
    """Genera el PDF del periodo. Cada descarga nueva queda registrada en la tabla `reportes`.
    Con ?id=N se vuelve a descargar un reporte ya registrado, sin crear otro registro."""
    id_existente = request.args.get('id', type=int)
    if id_existente:
        guardado = Reporte.obtener(id_existente)
        if not guardado:
            flash('Ese reporte no existe.')
            return redirect(url_for('reportes_modulo.reportes'))
        desde, hasta = guardado['fecha_desde'], guardado['fecha_hasta']
        id_reporte = id_existente
        datos = Reporte.resumen(desde, hasta)
    else:
        desde, hasta = _rango_solicitado()
        datos = Reporte.resumen(desde, hasta)
        id_reporte = Reporte.registrar(datos, session.get('id_usuario'))

    pdf = generar_pdf(datos, generado_por=session.get('nombre'), id_reporte=id_reporte)
    nombre = f"reporte_{desde.isoformat()}_{hasta.isoformat()}.pdf"
    return Response(pdf, mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment; filename="{nombre}"'})
