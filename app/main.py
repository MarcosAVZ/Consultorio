# main.py — Opción A (importar el módulo actions completo, sin paquete 'app')

import tkinter as tk
from tkinter import messagebox

import actions  # 👈 importás el MÓDULO entero
from paths import get_paths
from db import init_db
from ui import (
    build_form, build_actions, build_table,
    bind_context_menu, cargar_desde_tabla, clear_form
)
from backup_drive import can_backup


def main():
    paths = get_paths()
    conn, cur = init_db(paths["DB_NAME"])

    root = tk.Tk()
    root.title("Consultorio Gerontológico Integral - Dra. Zulma Cabrera")
    root.geometry("1200x700")

    # UI
    form_frame, fields = build_form(root)
    right, table, q_var, crit_var = build_table(root)

    # Botonera
    btn_bkp = build_actions(form_frame, handlers={
        "guardar":    lambda: actions.guardar(cur, conn, fields, on_done=lambda: actions.refresh_table(table, cur)),
        "actualizar": lambda: actions.actualizar(cur, conn, table, fields, on_done=lambda: actions.refresh_table(table, cur)),
        "borrar":     lambda: actions.borrar(cur, conn, table, on_done=lambda: actions.refresh_table(table, cur), fields=fields),
        "pdf":        lambda: actions.generar_pdf_action(paths, table),  # 👈 ahora sí: actions.<función>
        "limpiar":    lambda: clear_form(fields),
        "csv":        lambda: actions.export_csv(cur),
        "backup":     lambda: actions.backup_now_action(paths),
    })
    if not can_backup(paths):
        btn_bkp.state(["disabled"])

    # Cargar al formulario desde la tabla
    table.bind("<Double-1>", lambda e: cargar_desde_tabla(table, fields))
    table.bind("<<TreeviewSelect>>", lambda e: cargar_desde_tabla(table, fields))

    # Buscar/filtrar
    def _apply_filter(*_):
        actions.apply_filter(table, cur, q_var.get().strip(), crit_var.get())

    root.bind_all("<Return>", lambda e: _apply_filter() if e.widget is not root else None)

    # Menú contextual
    bind_context_menu(root, list(fields.values()))

    # Datos iniciales
    actions.refresh_table(table, cur)

    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        messagebox.showerror("Error fatal", str(e))
