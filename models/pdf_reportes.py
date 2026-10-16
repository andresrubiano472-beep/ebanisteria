"""Generación del reporte en PDF con fpdf (paquete fpdf2)."""
import os
from datetime import datetime

from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(BASE_DIR, 'Static', 'img', 'logoproyecto.png')

NARANJA = (242, 140, 0)
OSCURO = (35, 35, 35)
GRIS = (245, 245, 245)


def _t(valor, largo=None):
    """Texto seguro para las fuentes estándar de PDF (latin-1): conserva tildes y ñ."""
    if valor is None or valor == '':
        valor = '-'
    texto = str(valor).replace('—', '-').replace('–', '-').replace('•', '-')
    texto = texto.encode('latin-1', 'replace').decode('latin-1')
    if largo and len(texto) > largo:
        texto = texto[:largo - 1] + '.'
    return texto


class _ReportePDF(FPDF):
    def header(self):
        if os.path.exists(LOGO):
            self.image(LOGO, x=10, y=8, h=14)
        self.set_xy(28, 8)
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(*OSCURO)
        self.cell(0, 7, 'AssetMate - Taller de Ebanisteria', new_x='LMARGIN', new_y='NEXT')
        self.set_x(28)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(110, 110, 110)
        self.cell(0, 5, 'Reporte de prestamos de herramientas', new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(*NARANJA)
        self.set_line_width(0.6)
        self.line(10, 25, 200, 25)
        self.set_y(30)

    def footer(self):
        self.set_y(-14)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 8, f'ITIPISTA  |  Pagina {self.page_no()} de {{nb}}', align='C')


def _titulo(pdf, texto):
    pdf.ln(3)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(*NARANJA)
    pdf.cell(0, 7, _t(texto), new_x='LMARGIN', new_y='NEXT')
    pdf.set_text_color(*OSCURO)


def _tabla(pdf, columnas, filas, vacio='Sin datos en este periodo.'):
    """columnas = [(titulo, ancho, alineacion, largo_maximo)]"""
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(*OSCURO)
    pdf.set_text_color(255, 255, 255)
    for titulo, ancho, _, _ in columnas:
        pdf.cell(ancho, 7, _t(titulo), border=0, align='C', fill=True)
    pdf.ln(7)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*OSCURO)
    if not filas:
        pdf.set_fill_color(*GRIS)
        pdf.cell(sum(c[1] for c in columnas), 8, _t(vacio), align='C', fill=True, new_x='LMARGIN', new_y='NEXT')
        return
    for i, fila in enumerate(filas):
        pdf.set_fill_color(*GRIS)
        for (_, ancho, alin, largo), valor in zip(columnas, fila):
            pdf.cell(ancho, 7, _t(valor, largo), border=0, align=alin, fill=(i % 2 == 0))
        pdf.ln(7)


def generar_pdf(datos, generado_por=None, id_reporte=None):
    """Devuelve los bytes del PDF a partir del diccionario que entrega Reporte.resumen()."""
    pdf = _ReportePDF(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Datos generales del reporte
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(*OSCURO)
    pdf.cell(0, 8, _t(f"Periodo: {datos['desde'].strftime('%d/%m/%Y')} al {datos['hasta'].strftime('%d/%m/%Y')}"),
             new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(110, 110, 110)
    meta = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    if generado_por:
        meta += f" por {generado_por}"
    if id_reporte:
        meta += f"  |  Reporte No. {id_reporte}"
    pdf.cell(0, 5, _t(meta), new_x='LMARGIN', new_y='NEXT')

    # Tarjetas de resumen
    pdf.ln(4)
    c = datos['conteo']
    tarjetas = [
        ('Solicitudes', datos['prestamos']),
        ('Aprobadas', c.get('Aprobado', 0)),
        ('Devueltas', c.get('Devuelto', 0)),
        ('Rechazadas', c.get('Rechazado', 0)),
        ('Pendientes', c.get('Pendiente', 0)),
    ]
    ancho = 190 / len(tarjetas)
    y = pdf.get_y()
    for i, (nombre, valor) in enumerate(tarjetas):
        x = 10 + i * ancho
        pdf.set_fill_color(*GRIS)
        pdf.rect(x + 1, y, ancho - 2, 18, style='F')
        pdf.set_xy(x + 1, y + 2)
        pdf.set_font('Helvetica', 'B', 15)
        pdf.set_text_color(*NARANJA)
        pdf.cell(ancho - 2, 7, _t(valor), align='C')
        pdf.set_xy(x + 1, y + 10)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(ancho - 2, 5, _t(nombre), align='C')
    pdf.set_y(y + 22)

    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*OSCURO)
    pdf.cell(0, 5, _t(f"Inventario actual: {datos['herramientas']} herramientas activas  |  "
                      f"{datos['estudiantes']} estudiantes activos"), new_x='LMARGIN', new_y='NEXT')

    # Uso por herramienta (solo las que tuvieron movimiento)
    _titulo(pdf, 'Uso por herramienta')
    filas = [(h['herramienta'], h['solicitudes'] or 0, h['aprobados'] or 0)
             for h in datos['por_herramienta'] if (h['solicitudes'] or 0) > 0]
    _tabla(pdf, [('Herramienta', 110, 'L', 55), ('Solicitudes', 40, 'C', None), ('Aprobadas', 40, 'C', None)], filas)

    # Detalle de movimientos
    _titulo(pdf, 'Detalle de movimientos')
    filas = [(m['id_prestamo'], m['estudiante'], m['herramienta'],
              m['fecha_entrega'].strftime('%d/%m/%Y') if m['fecha_entrega'] else None,
              m['fecha_devolucion'].strftime('%d/%m/%Y') if m['fecha_devolucion'] else None,
              m['estado_solicitud']) for m in datos['recientes']]
    _tabla(pdf, [('ID', 12, 'C', None), ('Estudiante', 52, 'L', 28), ('Herramienta', 46, 'L', 24),
                 ('Solicitud', 25, 'C', None), ('Devolucion', 25, 'C', None), ('Estado', 30, 'C', None)],
           filas, 'No hubo movimientos en este periodo.')

    return bytes(pdf.output())
