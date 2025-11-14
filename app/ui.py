# ui.py
import os
import time
import shutil
import datetime as dt
import flet as ft

from db import init_db
from backup_drive import can_backup, backup_now
from actions import *

# --- Constantes y columnas de la BD (mismo orden que en db.py) ---
COLUMNS = (
    "id","nombre","dni","edad","domicilio","obra_social","numero_beneficio",
    "telefono","email","antecedentes_personales","antecedentes_familiares",
    "examen_fisico","diagnostico_presuntivo","evolucion_seguimiento","motivo_consulta"
)
HEADERS = {
    "id":"ID","nombre":"Nombre","dni":"DNI","edad":"Edad","domicilio":"Domicilio",
    "obra_social":"Obra Social","numero_beneficio":"N° Beneficio","telefono":"Teléfono","email":"Email",
    "antecedentes_personales":"Ant. Personales","antecedentes_familiares":"Ant. Familiares",
    "examen_fisico":"Examen Físico","diagnostico_presuntivo":"Diagnóstico Presuntivo",
    "evolucion_seguimiento":"Evolución/Seguimiento","motivo_consulta":"Motivo Consulta"
}

def _toast(page: ft.Page, msg: str):
    page.snack_bar = ft.SnackBar(ft.Text(msg))
    page.snack_bar.open = True
    page.update()

def _open_folder(path: str):
    try:
        if os.name == "nt":
            os.startfile(path)  # Windows
        else:
            import subprocess, sys
            if sys.platform == "darwin":
                subprocess.Popen(["open", path])      # macOS
            else:
                subprocess.Popen(["xdg-open", path])  # Linux
    except Exception:
        pass

def make_app(page: ft.Page, conn, cur, paths):
    # ---------- Setup ----------
    page.title = "Consultorio Gerontológico Integral - Dra. Zulma Cabrera"
    page.window_maximized = True
    page.theme_mode = "light"
    page.bgcolor = "#F4F1ED"

    # Guardamos conn/cur en sesión para poder reabrir tras importar BD
    page.session.set("conn", conn)
    page.session.set("cur", cur)

    # ---------- FORM (izquierda) ----------
    tf_nombre   = ft.TextField(label="Nombre",    expand=True)
    tf_dni      = ft.TextField(label="DNI",       expand=True)
    tf_edad     = ft.TextField(label="Edad",      expand=True)
    tf_dom      = ft.TextField(label="Domicilio", expand=True)
    tf_obra     = ft.TextField(label="Obra social", expand=True)
    tf_benef    = ft.TextField(label="N° beneficio", expand=True)
    tf_tel      = ft.TextField(label="Teléfono",  expand=True)
    tf_email    = ft.TextField(label="Email",     expand=True)
    tf_motivo   = ft.TextField(label="Motivo de consulta", expand=True)

    ta_ant_pers = ft.TextField(label="Antecedentes personales", multiline=True, min_lines=3, max_lines=5)
    ta_ant_fam  = ft.TextField(label="Antecedentes familiares", multiline=True, min_lines=3, max_lines=5)
    ta_examen   = ft.TextField(label="Examen físico",           multiline=True, min_lines=3, max_lines=5)
    ta_diag     = ft.TextField(label="Diagnóstico presuntivo",  multiline=True, min_lines=3, max_lines=5)
    ta_evol     = ft.TextField(label="Evolución / seguimiento", multiline=True, min_lines=3, max_lines=5)

    # Para saber qué fila está seleccionada actualmente
    selected_row_values = {"values": None}  # dict mutable para cerrar sobre él

    def clear_form():
        for w in [tf_nombre, tf_dni, tf_edad, tf_dom, tf_obra, tf_benef, tf_tel, tf_email, tf_motivo,
                  ta_ant_pers, ta_ant_fam, ta_examen, ta_diag, ta_evol]:
            w.value = ""
        selected_row_values["values"] = None
        page.update()

    def get_form_data():
        return {
            "nombre": tf_nombre.value.strip(),
            "dni": tf_dni.value.strip(),
            "edad": tf_edad.value.strip(),
            "domicilio": tf_dom.value.strip(),
            "obra_social": tf_obra.value.strip(),
            "numero_beneficio": tf_benef.value.strip(),
            "telefono": tf_tel.value.strip(),
            "email": tf_email.value.strip(),
            "motivo_consulta": tf_motivo.value.strip(),
            "antecedentes_personales": ta_ant_pers.value.strip(),
            "antecedentes_familiares": ta_ant_fam.value.strip(),
            "examen_fisico": ta_examen.value.strip(),
            "diagnostico_presuntivo": ta_diag.value.strip(),
            "evolucion_seguimiento": ta_evol.value.strip(),
        }

    # ---------- TABLA (derecha) ----------
    table_columns = [
        ft.DataColumn(ft.Text(HEADERS["nombre"])),
        ft.DataColumn(ft.Text(HEADERS["dni"])),
        ft.DataColumn(ft.Text(HEADERS["edad"])),
        ft.DataColumn(ft.Text(HEADERS["obra_social"])),
        ft.DataColumn(ft.Text(HEADERS["numero_beneficio"])),
        ft.DataColumn(ft.Text(HEADERS["telefono"])),
        ft.DataColumn(ft.Text(HEADERS["motivo_consulta"])),
    ]

    def load_to_form(values):
        tf_nombre.value = values[1] or ""
        tf_dni.value    = values[2] or ""
        tf_edad.value   = str(values[3] or "")
        tf_dom.value    = values[4] or ""
        tf_obra.value   = values[5] or ""
        tf_benef.value  = values[6] or ""
        tf_tel.value    = values[7] or ""
        tf_email.value  = values[8] or ""
        ta_ant_pers.value = values[9] or ""
        ta_ant_fam.value  = values[10] or ""
        ta_examen.value   = values[11] or ""
        ta_diag.value     = values[12] or ""
        ta_evol.value     = values[13] or ""
        tf_motivo.value   = values[14] or ""
        selected_row_values["values"] = values
        page.update()

    table = ft.DataTable(
        columns=table_columns,
        rows=[],
        heading_row_height=36,
        data_row_max_height=64,
        show_checkbox_column=False,
    )

    def table_set_rows(rows):
        table.rows = []
        visible_indexes = [1, 2, 3, 5, 6, 7, 14 ]
        def on_cell_tap(e, values):
            load_to_form(values)
        for r in rows:
            cells = [
                ft.DataCell(
                    ft.Text(str(r[i] or "")),
                    on_tap=lambda e, v=r: on_cell_tap(e, v)
                )
                for i in visible_indexes
            ]
            table.rows.append(ft.DataRow(cells=cells))
        page.update()

    def refresh_table():
        _cur = page.session.get("cur") or cur
        _cur.execute("SELECT * FROM historias")
        table_set_rows(_cur.fetchall())

    def after_refresh():
        refresh_table()

    # ---------- BÚSQUEDA ----------
    q_field = ft.TextField(label="Buscar", width=260)
    crit_dd = ft.Dropdown(
        label="criterio",
        value="nombre",
        options=[ft.dropdown.Option("nombre"), ft.dropdown.Option("dni")],
        width=140
    )
    def apply_filter(_=None):
        _cur = page.session.get("cur") or cur
        q = (q_field.value or "").strip()
        crit = crit_dd.value or "nombre"
        if q:
            _cur.execute(f"SELECT * FROM historias WHERE {crit} LIKE ?", (f"%{q}%",))
        else:
            _cur.execute("SELECT * FROM historias")
        table_set_rows(_cur.fetchall())

    q_field.on_submit = apply_filter


    # ---------- MENÚ ÚNICO (BD + PDFs + Backup) ----------
    DB_EXTS = ["db", "sqlite", "sqlite3"]
    open_db_picker  = ft.FilePicker()
    save_db_picker  = ft.FilePicker()
    pick_pdf_dir    = ft.FilePicker()  # usaremos get_directory_path()
    page.overlay.extend([open_db_picker, save_db_picker, pick_pdf_dir])

    def _on_import_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        src = e.files[0].path
        try:
            os.makedirs(os.path.dirname(paths["DB_NAME"]), exist_ok=True)
            # Cerrar conexión actual
            old_conn = page.session.get("conn")
            if old_conn:
                try:
                    old_conn.commit()
                    old_conn.close()
                except:
                    pass
            # Copiar BD
            shutil.copy2(src, paths["DB_NAME"])
            # Re-abrir
            new_conn, new_cur = init_db(paths["DB_NAME"])
            page.session.set("conn", new_conn)
            page.session.set("cur", new_cur)
            refresh_table()
            _toast(page, "Base de datos importada correctamente.")
        except Exception as ex:
            _toast(page, f"Error importando BD: {ex}")

    def _on_export_result(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        try:
            shutil.copy2(paths["DB_NAME"], e.path)
            _toast(page, "Copia de seguridad exportada.")
        except Exception as ex:
            _toast(page, f"Error exportando BD: {ex}")

    def _on_pdf_dir_result(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        try:
            os.makedirs(e.path, exist_ok=True)
            paths["PDFS_DIR"] = e.path  # <- actualizamos destino de PDFs
            _toast(page, f"Carpeta de PDFs actualizada:\n{e.path}")
        except Exception as ex:
            _toast(page, f"No se pudo actualizar la carpeta de PDFs: {ex}")

    open_db_picker.on_result = _on_import_result
    save_db_picker.on_result = _on_export_result
    pick_pdf_dir.on_result   = _on_pdf_dir_result

    def do_import(_: ft.ControlEvent):
        open_db_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=DB_EXTS,
            dialog_title="Seleccionar archivo de base de datos"
        )

    def do_export(_: ft.ControlEvent):
        fname = f"consultorio_backup_{time.strftime('%Y%m%d_%H%M%S')}.db"
        save_db_picker.save_file(
            file_name=fname,
            allowed_extensions=["db"],
            dialog_title="Guardar copia de la base de datos"
        )

    def do_select_pdf_dir(_: ft.ControlEvent):
        pick_pdf_dir.get_directory_path(
            dialog_title="Seleccionar carpeta para guardar PDFs"
        )

    def do_open_pdf_dir(_: ft.ControlEvent):
        if paths.get("PDFS_DIR"):
            _open_folder(paths["PDFS_DIR"])

    def do_backup_now(_: ft.ControlEvent):
        if can_backup(paths):
            backup_now_action(paths, page)
        else:
            _toast(page, "Backup no disponible: falta PyDrive2 o client_secrets.json")

    # Menú único (tres puntitos)
    more_menu = ft.PopupMenuButton(
        items=[
            ft.PopupMenuItem(text="Importar BD…",        on_click=do_import),
            ft.PopupMenuItem(text="Exportar BD…",        on_click=do_export),
            ft.PopupMenuItem(),  # separador
            ft.PopupMenuItem(text="Seleccionar carpeta de PDFs…", on_click=do_select_pdf_dir),
            ft.PopupMenuItem(text="Abrir carpeta de PDFs",        on_click=do_open_pdf_dir),
            ft.PopupMenuItem(),  # separador
            ft.PopupMenuItem(text="Backup ahora", on_click=do_backup_now, disabled=not can_backup(paths)),
        ],
        tooltip="Opciones",
    )

    # Creamos (o reemplazamos) la AppBar con un solo menú
    page.appbar = ft.AppBar(
        title=ft.Text("Consultorio Gerontológico Integral"),
        center_title=False,
        actions=[more_menu],
    )

    # ---------- Layout ----------
    left_form = ft.Column(
        controls=[
            tf_nombre, tf_dni, tf_edad, tf_dom, tf_obra, tf_benef, tf_tel, tf_email, tf_motivo,
            ta_ant_pers, ta_ant_fam, ta_examen, ta_diag, ta_evol,
            ft.Row([
                ft.ElevatedButton(
                    "Guardar", bgcolor="#B0E0A8",
                    on_click=lambda e: guardar(
                        page.session.get("cur") or cur,
                        page.session.get("conn") or conn,
                        get_form_data, clear_form, after_refresh, page
                    ),
                    expand=1
                ),
                ft.ElevatedButton(
                    "Actualizar",
                    on_click=lambda e: actualizar(
                        page.session.get("cur") or cur,
                        page.session.get("conn") or conn,
                        selected_row_values, get_form_data, clear_form, after_refresh, page
                    ),
                    expand=1
                ),
            ], spacing=10),
            ft.Row([
                ft.ElevatedButton(
                    "Borrar",
                    on_click=lambda e: accionBorrar(
                        page, selected_row_values,
                        page.session.get("cur") or cur,
                        page.session.get("conn") or conn,
                        clear_form, after_refresh
                    ),
                    expand=1
                ),
                ft.ElevatedButton(
                    "Generar PDF",
                    on_click=lambda e: generar_pdf_action(paths, selected_row_values, page),
                    expand=1
                ),
            ], spacing=10),
            ft.Row([
                ft.ElevatedButton("Limpiar", on_click=lambda e: clear_form(), expand=1),
            ], spacing=10),
            # Eliminado el botón "Backup ahora" del panel (está en el menú)
        ],
        expand=True,
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
    )

    right_panel = ft.Column(
        controls=[
            ft.Row([q_field, crit_dd,
                    ft.FilledButton("Buscar", on_click=apply_filter),
                    ft.FilledButton("Actualizar", on_click=lambda e: refresh_table()),
                    ], spacing=10),
            ft.Container(
                content=ft.ListView(
                    controls=[table],
                    expand=True,
                ),
                expand=True,
            )
        ],
        expand=True,
        spacing=8,
    )

    page.add(
        ft.ResponsiveRow(
            controls=[
                ft.Container(left_form, col={"xs": 12, "md": 5, "lg": 4}, bgcolor="#F4F1ED"),
                ft.Container(right_panel, col={"xs": 12, "md": 7, "lg": 8}, bgcolor="#F4F1ED"),
            ],
            expand=True
        )
    )

    # Datos iniciales
    refresh_table()

    # Cerrar conexión al salir (la actual en sesión)
    def on_close(e):
        try:
            _conn = page.session.get("conn") or conn
            _conn.commit(); _conn.close()
        except:
            pass
        page.window_destroy()
    page.on_close = on_close
