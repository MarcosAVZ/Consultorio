import csv
import datetime as dt
import flet as ft

from validators import validar_campos
from pdf_utils import generar_pdf
from backup_drive import backup_now, can_backup

# ---------------- Tabla ----------------

#se podria agregar aqui los refresh , no lo se la verdad

# ---------------- CRUD ----------------

def guardar(cur, conn, get_form_data, clear_form, after_refresh, page: ft.Page):
    print("[DEBUG] Se toco el boton guardar")
    data = get_form_data()
    ok, msg = validar_campos(data)
    if not ok:
        print("[DEBUG] no pasa la validacion")
        _notify(f"Validación {msg}", page); return

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
    print("[DEBUG] Se guardo el nuevo paciente")
    _notify("Historia clínica guardada",page)

def actualizar(cur, conn, selected_row_values, get_form_data, clear_form, after_refresh, page: ft.Page):
    values = selected_row_values.get("values")
    if not values:
        _notify( "ATENCIÓN: Seleccioná una historia para actualizar",page); return
    row_id = int(values[0])

    data = get_form_data()
    ok, msg = validar_campos(data)
    if not ok:
        _notify(f"Validación {msg}", page); return

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
    _notify( "Historia clínica actualizada", page)

def accionBorrar(page,selected_row_values,cur, conn,clear_form,after_refresh):
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        values = selected_row_values.get("values")
        def cerrar_banner(e):
            page.close(banner)

        def confirmar_borrado(e):
            page.close(banner)
            
            if not values:
                print("[DEBUG] No tiene valor deberia aparecer el snackbar")
                _notify("Seleccioná una fila primero", page)
                return
            try:
                row_id = int(values[0])
                cur.execute("DELETE FROM historias WHERE id=?", (row_id,))
                print("[DEBUG] rowcount after DELETE:", cur.rowcount)
                conn.commit()
                clear_form()
                after_refresh()
                _notify("Historia clínica eliminada", page)
            except Exception as ex:
                _notify(f"Error al borrar: {ex}", page)
              

        banner = ft.Banner(
            bgcolor=ft.Colors.AMBER_100,
            leading=ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER, size=40),
            content=ft.Text(
                value="¿Estás seguro de que querés eliminar este registro?",
                color=ft.Colors.BLACK,
            ),
            actions=[
                ft.TextButton(text="Cancelar", on_click=cerrar_banner),
                ft.TextButton(text="Borrar", style=ft.ButtonStyle(color=ft.Colors.RED), on_click=confirmar_borrado),
            ],
        )

        page.open(banner)


# ---------------- Exportar / PDF / Backup ----------------

def export_csv(cur, page: ft.Page, file_picker: ft.FilePicker):
    cur.execute("SELECT * FROM historias"); rows = cur.fetchall()
    headers = [d[0] for d in cur.description]
    suggested = f"historias_{dt.datetime.now():%Y%m%d_%H%M%S}.csv"

    def save_result(e: ft.FilePickerResultEvent):
        if not e.path: return
        with open(e.path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";"); w.writerow(headers); w.writerows(rows)
        _notify(page, f"Se exportaron {len(rows)} filas a:\n{e.path}")

    file_picker.on_save = save_result
    file_picker.save_file(file_name=suggested, allowed_extensions=["csv"])

def generar_pdf_action(paths, selected_row_values, page: ft.Page):
    values = selected_row_values.get("values")
    if not values:
        _warn(page, "Atención", "Seleccioná una historia para generar PDF"); return
    try:
        out = generar_pdf(paths, values)
        _notify(page, f"PDF guardado en:\n{out}")
    except Exception as ex:
        _err(page, "Error PDF", str(ex))

def backup_now_action(paths, page):
    print("[DEBUG] Se toco el boton backup")
    if not can_backup(paths):
        print("[DEBUG] No tiene pydrive2 o client_secrets,json")
        _notify(page,"Falta PyDrive2 o client_secrets.json"); return
    try:
        backup_now(paths)
        print("[DEBUG] entro en de copia de seguridad")
        _notify("Copia de seguridad subida a Google Drive", page)
    except Exception as ex:
        _err(page, "Backup", str(ex))

# ---------------- Helpers UI (Flet) ----------------

def _notify(msg: str, page: ft.Page):
        try:
            page.open(ft.SnackBar(ft.Text(msg)))
            page.update()
        except Exception:
            page.open(ft.SnackBar(ft.Text(msg), open=True))
            page.update()
            
#-------------------------

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