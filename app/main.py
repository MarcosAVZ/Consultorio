# main.py
import tkinter as tk
from tkinter import messagebox

from paths import get_paths
from db import init_db
from ui import build_form, build_actions, build_table, bind_context_menu, cargar_desde_tabla
from actions import (refresh_table, apply_filter, guardar, actualizar, borrar,
                     export_csv, generar_pdf_action, backup_now_action)
from backup_drive import can_backup

def main():
    paths = get_paths()
    conn, cur = init_db(paths["DB_NAME"])

    root = tk.Tk()
    root.title("Consultorio Gerontológico Integral - Dra. Zulma Cabrera")
    root.geometry("1200x700")

    # === SCROLL PRINCIPAL ===
    main_canvas = tk.Canvas(root)
    main_scroll = tk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
    scrollable_frame = tk.Frame(main_canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: main_canvas.configure(
            scrollregion=main_canvas.bbox("all")
        )
    )

    main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    main_canvas.configure(yscrollcommand=main_scroll.set)

    main_canvas.pack(side="left", fill="both", expand=True)
    main_scroll.pack(side="right", fill="y")

    def _on_mousewheel(event):
        main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    root.bind_all("<MouseWheel>", _on_mousewheel)


    # === CONTENIDO DE LA INTERFAZ ===
    form_frame, fields = build_form(scrollable_frame)
    right, table, q_var, crit_var = build_table(scrollable_frame)


    # Botonera
    btn_bkp = build_actions(form_frame, handlers={
        "guardar":   lambda: guardar(cur, conn, fields, on_done=lambda: refresh_table(table, cur)),
        "actualizar":lambda: actualizar(cur, conn, table, fields, on_done=lambda: refresh_table(table, cur)),
        "borrar":    lambda: borrar(cur, conn, table, on_done=lambda: refresh_table(table, cur), fields=fields),
        "pdf":       lambda: generar_pdf_action(paths, table),
        "limpiar":   lambda: [w.delete(0, tk.END) if hasattr(w, 'delete') else None for w in fields.values()],
        "csv":       lambda: export_csv(cur),
        "backup":    lambda: backup_now_action(paths),
    })
    if not can_backup(paths):
        btn_bkp.state(["disabled"])

    # Cargar al formulario desde la tabla
    table.bind("<Double-1>", lambda e: cargar_desde_tabla(table, fields))
    table.bind("<<TreeviewSelect>>", lambda e: cargar_desde_tabla(table, fields))

    # Buscar/filtrar
    def _apply_filter(*_):
        apply_filter(table, cur, q_var.get().strip(), crit_var.get())
    root.bind_all("<Return>", lambda e: _apply_filter() if e.widget is not root else None)

    # Menú contextual
    bind_context_menu(root, list(fields.values()))

    # Datos iniciales
    refresh_table(table, cur)

    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        messagebox.showerror("Error fatal", str(e))
