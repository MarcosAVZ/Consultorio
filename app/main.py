# main.py
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

import actions
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

    # Ventana con tema y maximizada
    root = ttk.Window(themename="flatly")
    root.title("Consultorio Gerontológico Integral - Dra. Zulma Cabrera")
    root.state("zoomed")

    # Estilos sobrios + más separación en la tabla
    style = ttk.Style()
    style.configure("Treeview", rowheight=30, padding=6, font=("Segoe UI", 10))
    style.configure("Treeview.Heading", padding=(10, 8), font=("Segoe UI", 10, "bold"))

    # ----- Menú superior -----
    menubar = tk.Menu(root)
    m_archivo = tk.Menu(menubar, tearoff=0)
    m_archivo.add_command(
        label="Backup ahora",
        command=lambda: actions.backup_now_action(paths),
        state=("normal" if can_backup(paths) else "disabled"),
    )
    m_archivo.add_separator()
    m_archivo.add_command(label="Salir", command=root.destroy)
    menubar.add_cascade(label="Archivo", menu=m_archivo)

    m_ayuda = tk.Menu(menubar, tearoff=0)
    m_ayuda.add_command(label="Acerca de…", command=lambda: messagebox.showinfo(
        "Acerca de",
        "Consultorio Gerontológico Integral\n© 2025",
    ))
    menubar.add_cascade(label="Ayuda", menu=m_ayuda)
    root.config(menu=menubar)
    # --------------------------

    # Scroll principal (igual a tu versión)
    main_canvas = tk.Canvas(root)
    main_scroll = ttk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
    scrollable_frame = ttk.Frame(main_canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
    )
    main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    main_canvas.configure(yscrollcommand=main_scroll.set)
    main_canvas.pack(side="left", fill="both", expand=True)
    main_scroll.pack(side="right", fill="y")

    def _on_mousewheel(event):
        main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    root.bind_all("<MouseWheel>", _on_mousewheel)

    # UI
    form_frame, fields = build_form(scrollable_frame)
    right, table, q_var, crit_var = build_table(scrollable_frame)

    # Botonera (sin CSV, sin Backup)
    btn_bkp = build_actions(form_frame, handlers={
        "guardar":    lambda: actions.guardar(cur, conn, fields, on_done=lambda: actions.refresh_table(table, cur)),
        "actualizar": lambda: actions.actualizar(cur, conn, table, fields, on_done=lambda: actions.refresh_table(table, cur)),
        "borrar":     lambda: actions.borrar(cur, conn, table, on_done=lambda: actions.refresh_table(table, cur), fields=fields),
        "pdf":        lambda: actions.generar_pdf_action(paths, table),
        "limpiar":    lambda: clear_form(fields),
    })
    # quitamos el estado del botón backup (ya está en el menú)

    # Cargar al formulario desde la tabla
    table.bind("<Double-1>", lambda e: cargar_desde_tabla(table, fields))
    table.bind("<<TreeviewSelect>>", lambda e: cargar_desde_tabla(table, fields))

    # Buscar/filtrar (Enter)
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
