# pdf_utils.py
import os
import re
import inspect
import datetime
from fpdf import FPDF

# Pillow (solo para mostrar el logo si existe)
try:
    from PIL import Image  # noqa: F401
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# Detecta si fpdf2.MultiCell soporta el kw 'split_only_by_whitespace'
_HAS_SPLIT = "split_only_by_whitespace" in inspect.signature(FPDF.multi_cell).parameters

TITLE = "Consultorio Gerontológico Integral - Dra. Zulma Cabrera"

# ------------------------- helpers de texto -------------------------
def _safe(s) -> str:
    if s is None:
        return ""
    return str(s).replace("\r", "").replace("\t", " ").strip()

def _latin1_safe(s: str) -> str:
    """Reemplaza caracteres fuera de latin-1 para evitar errores si no hay fuentes Unicode."""
    if not s:
        return ""
    s = (
        s.replace("\u2022", "- ")  # bullet
         .replace("\u2023", "- ")
         .replace("\u2013", "-")   # ndash
         .replace("\u2014", "-")   # mdash
         .replace("\u2018", "'").replace("\u2019", "'")
         .replace("\u201c", '"').replace("\u201d", '"')
    )
    try:
        s.encode("latin-1")
        return s
    except UnicodeEncodeError:
        return s.encode("latin-1", "replace").decode("latin-1")

def _hard_wrap_long_tokens(s: str, limit: int = 60) -> str:
    """Corta tokens sin espacios (URLs/códigos) para que entren en el ancho."""
    if not s:
        return ""
    parts = re.split(r"(\s+)", s)  # conserva separadores
    out = []
    for p in parts:
        if p.isspace():
            out.append(p)
        else:
            while len(p) > limit:
                out.append(p[:limit] + "-")
                out.append("\n")
                p = p[limit:]
            out.append(p)
    return "".join(out)

def _mc(pdf: FPDF, w, h, txt: str):
    """multi_cell compatible (fpdf2/pyfpdf). La fuente se configura afuera."""
    if not _HAS_SPLIT:
        txt = _hard_wrap_long_tokens(txt)
    if _HAS_SPLIT:
        pdf.multi_cell(w=w, h=h, txt=txt, split_only_by_whitespace=False)
    else:
        pdf.multi_cell(w=w, h=h, txt=txt)

# ------------------------- fuentes Unicode -------------------------
def _register_unicode_fonts(pdf: FPDF, base_dir: str) -> bool:
    """
    Registra DejaVuSans (Regular/Bold) desde ./fonts. Devuelve True si quedó OK.
    """
    fonts_dir = os.path.join(base_dir, "fonts")
    reg = os.path.join(fonts_dir, "DejaVuSans.ttf")
    bold = os.path.join(fonts_dir, "DejaVuSans-Bold.ttf")
    if os.path.exists(reg):
        try:
            pdf.add_font("DejaVu", "", reg, uni=True)
            if os.path.exists(bold):
                pdf.add_font("DejaVu", "B", bold, uni=True)
            return True
        except Exception:
            return False
    return False

# ------------------------- Footer -------------------------
class PDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_draw_color(220, 220, 220)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())

        # separador seguro: bullet si hay Unicode; si no, guion
        sep = " • " if getattr(self, "_unicode_ok", False) else " - "

        # fuente del footer (definida en generar_pdf)
        self.set_font(getattr(self, "_footer_font_name", "Arial"), "", 9)
        self.set_text_color(130, 130, 130)
        txt = f"Generado: {datetime.datetime.now():%d/%m/%Y %H:%M}{sep}Página {self.page_no()}"
        self.cell(0, 8, txt, 0, 0, "R")


# ------------------------- Layout -------------------------
def _header(pdf: PDF, paths: dict, nombre: str, FONT_BOLD: tuple, FONT_REG: tuple, norm):
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    content_w = pdf.w - pdf.l_margin - pdf.r_margin

    y0 = pdf.get_y()
    if PIL_AVAILABLE and os.path.exists(paths.get("LOGO_PATH", "")):
        try:
            pdf.image(paths["LOGO_PATH"], x=pdf.l_margin, y=y0, w=22)
        except Exception:
            pass

    pdf.set_xy(pdf.l_margin + 26, y0)
    pdf.set_font(*FONT_BOLD, size=14)
    pdf.cell(w=content_w - 26, h=6, txt=norm(TITLE), ln=1)

    pdf.set_font(*FONT_REG, size=11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(w=content_w - 26, h=5, txt=norm(f"Historia Clínica - {nombre}"), ln=1)
    pdf.set_text_color(0, 0, 0)

    pdf.ln(4)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(3)

# --- NUEVA versión POSICIONAL ---
def _kv_row_at(pdf, x: float, y: float, label: str, value: str,
               col_w: float, FONT_BOLD: tuple, FONT_REG: tuple, norm) -> float:
    """Dibuja una fila clave/valor en (x,y) y devuelve la nueva y."""
    # Label
    pdf.set_xy(x, y)
    pdf.set_font(*FONT_BOLD, size=11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(w=col_w, h=5, txt=norm(label), ln=0)  # ln=0: no mueve X/Y

    # Valor (debajo del label)
    y_val = y + 5
    pdf.set_xy(x, y_val)
    pdf.set_font(*FONT_REG, size=11)
    pdf.set_text_color(0, 0, 0)
    # MultiCell devuelve al inicio de línea; como usamos coordenadas absolutas,
    # no importa: sólo nos interesa cuánta altura consumió.
    y_before = pdf.get_y()
    _mc(pdf, col_w, 5.0, norm(value))
    y_after = pdf.get_y()

    # altura usada = (y_after - y_val). Si MultiCell no cambió Y (línea corta),
    # garantizamos al menos 5 pt + pequeño margen
    height_used = max(5.0, y_after - y_val)
    return y_val + height_used + 2  # +2 de separación


def _two_columns_short_fields(pdf, data: dict, FONT_BOLD: tuple, FONT_REG: tuple, norm):
    content_w = pdf.w - pdf.l_margin - pdf.r_margin
    gap = 8
    col_w = (content_w - gap) / 2
    x_left = pdf.l_margin
    x_right = pdf.l_margin + col_w + gap
    y_top = pdf.get_y()

    left_labels  = ["DNI", "Edad", "Domicilio", "Obra Social"]
    right_labels = ["N° Beneficio", "Teléfono", "Email", "Motivo de Consulta"]

    # Punteros de altura independientes por columna
    yL = y_top
    yR = y_top

    for k in left_labels:
        yL = _kv_row_at(pdf, x_left, yL, k, data[k], col_w, FONT_BOLD, FONT_REG, norm)

    for k in right_labels:
        yR = _kv_row_at(pdf, x_right, yR, k, data[k], col_w, FONT_BOLD, FONT_REG, norm)

    # Continuar debajo de la columna más larga
    pdf.set_y(max(yL, yR))


def _section(pdf: PDF, title: str, body: str, FONT_BOLD: tuple, FONT_REG: tuple, norm):
    content_w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_fill_color(240, 240, 240)
    pdf.set_draw_color(220, 220, 220)
    pdf.set_line_width(0.2)
    pdf.set_font(*FONT_BOLD, size=11)
    pdf.cell(content_w, 7, norm(title), ln=1, fill=True, border=1)
    pdf.ln(1)

    x = pdf.l_margin
    y = pdf.get_y()
    pdf.set_font(*FONT_REG, size=11)
    _mc(pdf, content_w, 5.5, norm(body))
    y2 = pdf.get_y()
    pdf.rect(x, y, content_w, y2 - y)

# ------------------------- API principal -------------------------
def generar_pdf(paths: dict, row_values: list | tuple):
    """
    row_values = [id, nombre, dni, edad, domicilio, obra_social, numero_beneficio,
                  telefono, email, antecedentes_personales, antecedentes_familiares,
                  examen_fisico, diagnostico_presuntivo, evolucion_seguimiento,
                  motivo_consulta]
    """
    if not row_values:
        raise ValueError("No hay datos seleccionados para PDF")

    os.makedirs(paths["PDFS_DIR"], exist_ok=True)

    data = {
        "Nombre": _safe(row_values[1]),
        "DNI": _safe(row_values[2]),
        "Edad": _safe(row_values[3]),
        "Domicilio": _safe(row_values[4]),
        "Obra Social": _safe(row_values[5]),
        "N° Beneficio": _safe(row_values[6]),
        "Teléfono": _safe(row_values[7]),
        "Email": _safe(row_values[8]),
        "Motivo de Consulta": _safe(row_values[14] or ""),
        "Antecedentes Personales": _safe(row_values[9] or ""),
        "Antecedentes Familiares": _safe(row_values[10] or ""),
        "Examen Físico": _safe(row_values[11] or ""),
        "Diagnóstico Presuntivo": _safe(row_values[12] or ""),
        "Evolución/Seguimiento": _safe(row_values[13] or ""),
    }

    pdf = PDF("P", "mm", "A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(True, 18)

    unicode_ok = _register_unicode_fonts(pdf, paths.get("BASE_DIR", os.getcwd()))
    pdf._unicode_ok = bool(unicode_ok)  # <-- bandera para el footer

    if unicode_ok:
        FONT_REG = ("DejaVu", "")
        FONT_BOLD = ("DejaVu", "B")
        norm = _safe
        pdf._footer_font_name = "DejaVu"
    else:
        FONT_REG = ("Arial", "")
        FONT_BOLD = ("Arial", "B")
        norm = _latin1_safe
        pdf._footer_font_name = "Arial"


    # Encabezado
    _header(pdf, paths, data["Nombre"], FONT_BOLD, FONT_REG, norm)

    # Dos columnas para datos cortos
    _two_columns_short_fields(pdf, data, FONT_BOLD, FONT_REG, norm)
    pdf.ln(4)

    # Secciones largas
    _section(pdf, "Antecedentes Personales", data["Antecedentes Personales"], FONT_BOLD, FONT_REG, norm)
    pdf.ln(3)
    _section(pdf, "Antecedentes Familiares", data["Antecedentes Familiares"], FONT_BOLD, FONT_REG, norm)
    pdf.ln(3)
    _section(pdf, "Examen Físico", data["Examen Físico"], FONT_BOLD, FONT_REG, norm)
    pdf.ln(3)
    _section(pdf, "Diagnóstico Presuntivo", data["Diagnóstico Presuntivo"], FONT_BOLD, FONT_REG, norm)
    pdf.ln(3)
    _section(pdf, "Evolución / Seguimiento", data["Evolución/Seguimiento"], FONT_BOLD, FONT_REG, norm)

    out = os.path.join(paths["PDFS_DIR"], f"Historia_{data['Nombre']}_{data['DNI']}.pdf")
    pdf.output(out)
    return out
