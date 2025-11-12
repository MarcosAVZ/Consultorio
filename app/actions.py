import csv
import datetime as dt
import flet as ft

from validators import validar_campos
from pdf_utils import generar_pdf
from backup_drive import backup_now, can_backup

# ---------------- Tabla ----------------

def refresh_table(cur, table_set_rows):
    cur.execute("SELECT * FROM historias")
    table_set_rows(cur.fetchall())

def apply_filter(cur, table_set_rows, q: str, crit: str):
    if q:
        cur.execute(f"SELECT * FROM historias WHERE {crit} LIKE ?", (f"%{q}%",))
    else:
        cur.execute("SELECT * FROM historias")
    table_set_rows(cur.fetchall())

# ---------------- CRUD ----------------

def guardar(cur, conn, get_form_data, clear_form, after_refresh, page: ft.Page):
    data = get_form_data()
    ok, msg = validar_campos(data)
    if not ok:
        _warn(page, "Validación", msg); return

    ordered = (
        data["nombre"], data["dni"], data["edad"], data["domicilio"], data["obra_social"],
        data["numero_beneficio"], data["telefono"], data["email"],
        data["antecedentes_personales"], data["antecedentes_familiares"],
        data["examen_fisico"], data["diagnostico_presuntivo"],
        data["evolucion_seguimiento"], data["motivo_consulta"]
    )
    cur.execute("""INSERT INTO historias
        (nombre,dni,edad,domicilio,obra_social,numero_beneficio,telefono,email,
         antecedentes_personales,antecedentes_familiares,examen_fisico,diagnostico_presuntivo,
         evolucion_seguimiento,motivo_consulta)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", ordered)
    conn.commit()
    clear_form(); after_refresh()
    _info(page, "Éxito", "Historia clínica guardada")

def actualizar(cur, conn, selected_row_values, get_form_data, clear_form, after_refresh, page: ft.Page):
    values = selected_row_values.get("values")
    if not values:
        _warn(page, "Atención", "Seleccioná una historia para actualizar"); return
    row_id = int(values[0])

    data = get_form_data()
    ok, msg = validar_campos(data)
    if not ok:
        _warn(page, "Validación", msg); return

    ordered = (
        data["nombre"], data["dni"], data["edad"], data["domicilio"], data["obra_social"],
        data["numero_beneficio"], data["telefono"], data["email"],
        data["antecedentes_personales"], data["antecedentes_familiares"],
        data["examen_fisico"], data["diagnostico_presuntivo"],
        data["evolucion_seguimiento"], data["motivo_consulta"], row_id
    )
    cur.execute("""UPDATE historias SET
        nombre=?, dni=?, edad=?, domicilio=?, obra_social=?, numero_beneficio=?, telefono=?, email=?,
        antecedentes_personales=?, antecedentes_familiares=?, examen_fisico=?, diagnostico_presuntivo=?,
        evolucion_seguimiento=?, motivo_consulta=? WHERE id=?""", ordered)
    conn.commit()
    clear_form(); after_refresh()
    _info(page, "Éxito", "Historia clínica actualizada")

def borrar(cur, conn, selected_row_values, clear_form, after_refresh, page: ft.Page):
    values = selected_row_values.get("values")
    if not values:
        _warn(page, "Atención", "Seleccioná una historia para borrar"); return

    def _do_delete(_e):
        try:
            row_id = int(values[0])
            cur.execute("DELETE FROM historias WHERE id=?", (row_id,))
            conn.commit()
            clear_form(); after_refresh()
            _snack(page, "Historia clínica eliminada")
        except Exception as ex:
            _err(page, "Error al borrar", str(ex))
        finally:
            _close_dialog(page)

    _confirm(page, "Confirmar", "¿Querés borrar esta historia clínica?", _do_delete)

# ---------------- Exportar / PDF / Backup ----------------

def export_csv(cur, page: ft.Page, file_picker: ft.FilePicker):
    cur.execute("SELECT * FROM historias"); rows = cur.fetchall()
    headers = [d[0] for d in cur.description]
    suggested = f"historias_{dt.datetime.now():%Y%m%d_%H%M%S}.csv"

    def save_result(e: ft.FilePickerResultEvent):
        if not e.path: return
        with open(e.path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";"); w.writerow(headers); w.writerows(rows)
        _snack(page, f"Se exportaron {len(rows)} filas a:\n{e.path}")

    file_picker.on_save = save_result
    file_picker.save_file(file_name=suggested, allowed_extensions=["csv"])

def generar_pdf_action(paths, selected_row_values, page: ft.Page):
    values = selected_row_values.get("values")
    if not values:
        _warn(page, "Atención", "Seleccioná una historia para generar PDF"); return
    try:
        out = generar_pdf(paths, values)
        _snack(page, f"PDF guardado en:\n{out}")
    except Exception as ex:
        _err(page, "Error PDF", str(ex))

def backup_now_action(paths, page: ft.Page):
    if not can_backup(paths):
        _warn(page, "Backup", "Falta PyDrive2 o client_secrets.json"); return
    try:
        backup_now(paths)
        _snack(page, "Copia de seguridad subida a Google Drive")
    except Exception as ex:
        _err(page, "Backup", str(ex))

# ---------------- Helpers UI (Flet) ----------------

def _info(page: ft.Page, title: str, msg: str):
    page.dialog = ft.AlertDialog(title=ft.Text(title), content=ft.Text(msg))
    page.dialog.open = True
    page.update()

def _snack(page: ft.Page, msg: str):
    page.snack_bar = ft.SnackBar(ft.Text(msg), open=True); page.update()

def _warn(page: ft.Page, title: str, msg: str):
    page.dialog = ft.AlertDialog(title=ft.Text(title), content=ft.Text(msg))
    page.dialog.open = True; page.update()

def _err(page: ft.Page, title: str, msg: str):
    _warn(page, title, msg)

def _confirm(page: ft.Page, title: str, msg: str, on_yes):
    page.dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(msg),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: _close_dialog(page)),
            ft.ElevatedButton("Aceptar", on_click=on_yes),
        ],
    )
    page.dialog.open = True; page.update()

def _close_dialog(page: ft.Page):
    if getattr(page, "dialog", None):
        page.dialog.open = False; page.update()