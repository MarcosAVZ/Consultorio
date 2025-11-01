# pdf_utils.py
import os
from fpdf import FPDF

# Pillow es opcional (solo para el logo)
try:
    from PIL import Image  # noqa: F401
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

def generar_pdf(paths: dict, row_values: list | tuple):
    """
    row_values: secuencia con el registro completo en el orden de la tabla:
        [id, nombre, dni, edad, domicilio, obra_social, numero_beneficio, telefono, email,
         antecedentes_personales, antecedentes_familiares, examen_fisico, diagnostico_presuntivo,
         evolucion_seguimiento, motivo_consulta]
    """
    if not row_values:
        raise ValueError("No hay datos seleccionados para PDF")

    pdf = FPDF('P','mm','A4')
    pdf.add_page()
    pdf.set_auto_page_break(True, 15)

    if PIL_AVAILABLE and os.path.exists(paths["LOGO_PATH"]):
        pdf.image(paths["LOGO_PATH"], x=10, y=8, w=40)

    pdf.set_font("Arial",'B',16)
    pdf.cell(0,10,f"Historia Clínica - {row_values[1]}", ln=True, align="C")

    pdf.set_font("Arial","",12)
    campos = ['DNI','Edad','Domicilio','Obra Social','N° Beneficio','Teléfono','Email','Motivo de Consulta',
              'Antecedentes Personales','Antecedentes Familiares','Examen Físico','Diagnóstico Presuntivo','Evolución/Seguimiento']
    for i, campo in enumerate(campos, start=2):
        pdf.ln(5)
        pdf.set_font("Arial",'B',12); pdf.multi_cell(0,6,campo)
        pdf.set_font("Arial","",12);  pdf.multi_cell(0,6,str(row_values[i] or ""))

    out = os.path.join(paths["PDFS_DIR"], f"Historia_{row_values[1]}_{row_values[2]}.pdf")
    pdf.output(out)
    return out
