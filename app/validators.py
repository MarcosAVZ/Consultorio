# validators.py
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validar_campos(data: dict):
    if not data.get('nombre'):
        return False, "El nombre es obligatorio."
    if not data.get('dni'):
        return False, "El DNI es obligatorio."

    dni_clean = re.sub(r"[^\d]", "", data['dni'])
    if not dni_clean.isdigit() or len(dni_clean) < 7:
        return False, "El DNI debe ser numérico (mínimo 7 dígitos)."

    if data.get('edad'):
        try:
            edad = int(data['edad'])
            if not (0 <= edad <= 120):
                return False, "La edad debe estar entre 0 y 120."
        except ValueError:
            return False, "La edad debe ser un número entero."

    if data.get('telefono'):
        if not re.fullmatch(r"[0-9 +\-()]{6,}", data['telefono']):
            return False, "El teléfono tiene un formato inválido."

    if data.get('email') and not EMAIL_RE.match(data['email']):
        return False, "El email no tiene un formato válido."

    return True, ""
