# ui.py
import csv
import datetime as dt
import flet as ft
#import actions as ACT

from backup_drive import can_backup,backup_now
from actions import *


# --- Constantes y columnas de la BD (mismo orden que en db.py/ui.py) ---
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


def make_app(page: ft.Page, conn, cur, paths):
    # ---------- Setup ----------

    print("[DEBUG] can_backup:", can_backup(paths))
    
    page.title = "Consultorio Gerontológico Integral - Dra. Zulma Cabrera"
    page.window_maximized = True
    page.theme_mode = "light"
    page.bgcolor="#F4F1ED"
    
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
        data = {
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
        return data

    # ---------- TABLA (derecha) ----------
    # Cabeceras
    table_columns = [
        #ft.DataColumn(ft.Text(HEADERS["id"])),
        ft.DataColumn(ft.Text(HEADERS["nombre"])),
        ft.DataColumn(ft.Text(HEADERS["dni"])),
        ft.DataColumn(ft.Text(HEADERS["edad"])),
        #ft.DataColumn(ft.Text(HEADERS["domicilio"])),
        ft.DataColumn(ft.Text(HEADERS["obra_social"])),
        ft.DataColumn(ft.Text(HEADERS["numero_beneficio"])),
        ft.DataColumn(ft.Text(HEADERS["telefono"])),
        #ft.DataColumn(ft.Text(HEADERS["email"])),
        #ft.DataColumn(ft.Text(HEADERS["antecedentes_personales"])),
        #ft.DataColumn(ft.Text(HEADERS["antecedentes_familiares"])),
        #ft.DataColumn(ft.Text(HEADERS["examen_fisico"])),
        #ft.DataColumn(ft.Text(HEADERS["diagnostico_presuntivo"])),
        #ft.DataColumn(ft.Text(HEADERS["evolucion_seguimiento"])),
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

    
    #table = ft.DataTable(columns=table_columns, rows=[], heading_row_height=36, data_row_max_height=64)-----
    
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
            # Cargar valores al formulario al tocar cualquier celda
            load_to_form(values)

        
        for r in rows:
            # cada celda reacciona al click y carga el form
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
        cur.execute("SELECT * FROM historias")
        table_set_rows(cur.fetchall())
        
    def after_refresh():
        cur.execute("SELECT * FROM historias")
        table_set_rows(cur.fetchall())

    # ---------- BÚSQUEDA ----------
    q_field = ft.TextField(label="Buscar", width=260)
    crit_dd = ft.Dropdown(
        label="criterio",
        value="nombre",
        options=[ft.dropdown.Option("nombre"), ft.dropdown.Option("dni")],
        width=140
    )
    def apply_filter(_=None):
        q = (q_field.value or "").strip()
        crit = crit_dd.value or "nombre"
        if q:
            cur.execute(f"SELECT * FROM historias WHERE {crit} LIKE ?", (f"%{q}%",))
        else:
            cur.execute("SELECT * FROM historias")
        table_set_rows(cur.fetchall())


    def refrescarTabla():
        rows = []

        visible_indexes = [1, 2, 3, 5, 6, 7, 14 ]

        def on_cell_tap(e, values):
            # Cargar valores al formulario al tocar cualquier celda
            load_to_form(values)

        
        for r in rows:
            # cada celda reacciona al click y carga el form
            cells = [
                ft.DataCell(
                    ft.Text(str(r[i] or "")),
                    on_tap=lambda e, v=r: on_cell_tap(e, v)
                )
                for i in visible_indexes
            ]
            rows.append(ft.DataRow(cells=cells))

        page.update()
        
       # cur.execute("SELECT * FROM historias")
        #table_set_rows(cur.fetchall())
    
    # Atajo Enter en el buscador
    q_field.on_submit = apply_filter

#----------
    # CSV con FilePicker
    fp = ft.FilePicker()
    page.overlay.append(fp)

    def export_csv_action(_=None):
        cur.execute("SELECT * FROM historias"); rows = cur.fetchall()
        headers = [d[0] for d in cur.description]
        # sugerir nombre
        suggested = f"historias_{dt.datetime.now():%Y%m%d_%H%M%S}.csv"
        def save_result(e: ft.FilePickerResultEvent):
            if not e.path: return
            with open(e.path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(headers); w.writerows(rows)
            page.snack_bar = ft.SnackBar(ft.Text(f"Se exportaron {len(rows)} filas a:\n{e.path}"), open=True); page.update()
        fp.on_save = save_result
        fp.save_file(file_name=suggested, allowed_extensions=["csv"])

    # ---------- Layout ----------
    # Columna izquierda (form) con scroll
    left_form = ft.Column(
        controls=[
            tf_nombre, tf_dni, tf_edad, tf_dom, tf_obra, tf_benef, tf_tel, tf_email, tf_motivo,
            ta_ant_pers, ta_ant_fam, ta_examen, ta_diag, ta_evol,
            ft.Row([
                ft.ElevatedButton("Guardar",bgcolor="#B0E0A8",on_click=lambda e: guardar(cur, conn, get_form_data, clear_form, after_refresh, page), expand=1),
                ft.ElevatedButton("Actualizar",on_click=lambda e: actualizar(cur, conn, selected_row_values, get_form_data, clear_form, after_refresh, page), expand=1),
            ], spacing=10),
            ft.Row([
                ft.ElevatedButton("Borrar",on_click=lambda e: accionBorrar(page, selected_row_values, cur, conn, clear_form, after_refresh), expand=1),
                ft.ElevatedButton("Generar PDF",on_click=lambda e: generar_pdf_action(paths, selected_row_values, page), expand=1),
            ], spacing=10),
            ft.Row([
                ft.ElevatedButton("Limpiar", on_click=lambda e: clear_form(), expand=1),
                ft.ElevatedButton("Exportar CSV",on_click=lambda e: export_csv(cur, page, fp), expand=1),
            ], spacing=10),
            
            ft.ElevatedButton("Backup ahora",on_click=lambda e: backup_now_action(paths, page),disabled=not can_backup(paths)),
        ],
        
        expand=True,
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
    )
    
        
        
    #ft.IconButton(ft.icons.SEARCH, tooltip="Buscar", on_click=apply_filter) Icons no funciona
    
    # Columna derecha (search + tabla) con scroll horizontal y vertical
    right_panel = ft.Column(
        controls=[
            ft.Row([q_field, crit_dd,
                    ft.FilledButton("Buscar", on_click=apply_filter),
                    ft.FilledButton("Actualizar", on_click = lambda e: refresh_table()),
                    ],spacing=10),
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
                ft.Container(left_form, col={"xs":12, "md":5, "lg":4},
                             bgcolor="#F4F1ED"),
                ft.Container(right_panel, col={"xs":12, "md":7, "lg":8},
                             bgcolor="#F4F1ED"),
            ],
            expand=True
        )
    )

    # Datos iniciales
    refresh_table()

    # Cerrar conexión al salir
    def on_close(e):
        try:
            conn.commit(); conn.close()
        except: pass
        page.window_destroy()
    page.on_close = on_close