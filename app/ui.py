# ui.py
import tkinter as tk
from tkinter import ttk, scrolledtext

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
WIDTHS = {
    "id":60,"nombre":160,"dni":110,"edad":60,"domicilio":180,"obra_social":120,"numero_beneficio":120,
    "telefono":110,"email":160,"antecedentes_personales":220,"antecedentes_familiares":220,
    "examen_fisico":220,"diagnostico_presuntivo":220,"evolucion_seguimiento":240,"motivo_consulta":200
}

def build_form(parent):
    frame = ttk.Frame(parent, padding=10); frame.pack(side=tk.LEFT, fill=tk.Y)

    def fila_entry(row, label, width=30):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=(0,6), pady=3)
        e = ttk.Entry(frame, width=width); e.grid(row=row, column=1, sticky="ew", pady=3); return e

    def fila_text(row, label, height=4, width=40):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="nw", padx=(0,6), pady=(8,3))
        t = scrolledtext.ScrolledText(frame, width=width, height=height, wrap=tk.WORD)
        t.grid(row=row, column=1, sticky="ew", pady=(8,3)); return t

    fields = {
        "nombre": fila_entry(0, "Nombre"),
        "dni": fila_entry(1, "DNI"),
        "edad": fila_entry(2, "Edad"),
        "domicilio": fila_entry(3, "Domicilio"),
        "obra_social": fila_entry(4, "Obra social"),
        "numero_beneficio": fila_entry(5, "N° beneficio"),
        "telefono": fila_entry(6, "Teléfono"),
        "email": fila_entry(7, "Email"),
        "motivo_consulta": fila_entry(8, "Motivo de consulta"),
        "antecedentes_personales": fila_text(9, "Antecedentes personales"),
        "antecedentes_familiares": fila_text(10, "Antecedentes familiares"),
        "examen_fisico": fila_text(11, "Examen físico"),
        "diagnostico_presuntivo": fila_text(12, "Diagnóstico presuntivo"),
        "evolucion_seguimiento": fila_text(13, "Evolución / seguimiento"),
    }
    frame.columnconfigure(1, weight=1)
    return frame, fields

def get_form_data(fields):
    data = {k: fields[k].get().strip() for k in
            ["nombre","dni","edad","domicilio","obra_social","numero_beneficio","telefono","email","motivo_consulta"]}
    data["antecedentes_personales"] = fields["antecedentes_personales"].get("1.0", tk.END).strip()
    data["antecedentes_familiares"] = fields["antecedentes_familiares"].get("1.0", tk.END).strip()
    data["examen_fisico"] = fields["examen_fisico"].get("1.0", tk.END).strip()
    data["diagnostico_presuntivo"] = fields["diagnostico_presuntivo"].get("1.0", tk.END).strip()
    data["evolucion_seguimiento"] = fields["evolucion_seguimiento"].get("1.0", tk.END).strip()
    return data

def clear_form(fields):
    for w in fields.values():
        if isinstance(w, (tk.Text, scrolledtext.ScrolledText)):
            w.delete("1.0", tk.END)
        else:
            w.delete(0, tk.END)

def build_actions(parent, handlers):
    actions = ttk.Frame(parent, padding=(0,10,0,0))
    actions.grid(row=14, column=0, columnspan=2, sticky="ew")
    actions.columnconfigure(0, weight=1); actions.columnconfigure(1, weight=1)

    ttk.Button(actions, text="Guardar",     command=handlers["guardar"]).grid(   row=0, column=0, sticky="ew", padx=(0,6), pady=4)
    ttk.Button(actions, text="Actualizar",  command=handlers["actualizar"]).grid(row=0, column=1, sticky="ew", padx=(6,0), pady=4)
    ttk.Button(actions, text="Borrar",      command=handlers["borrar"]).grid(    row=1, column=0, sticky="ew", padx=(0,6), pady=4)
    ttk.Button(actions, text="Generar PDF", command=handlers["pdf"]).grid(       row=1, column=1, sticky="ew", padx=(6,0), pady=4)
    ttk.Button(actions, text="Limpiar",     command=handlers["limpiar"]).grid(   row=2, column=0, columnspan=2, sticky="ew", pady=(6,0))
    ttk.Button(actions, text="Exportar CSV",command=handlers["csv"]).grid(       row=3, column=0, sticky="ew", padx=(0,6), pady=4)
    btn_bkp = ttk.Button(actions, text="Backup ahora", command=handlers["backup"])
    btn_bkp.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(6,0))
    return btn_bkp

def build_table(root):
    right = ttk.Frame(root, padding=10); right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # buscador
    search_bar = ttk.Frame(right); search_bar.pack(side=tk.TOP, fill=tk.X, pady=(0,8))
    tk.Label(search_bar, text="Buscar:").pack(side=tk.LEFT, padx=(0,6))
    q_var = tk.StringVar(); ent = ttk.Entry(search_bar, textvariable=q_var, width=30); ent.pack(side=tk.LEFT)
    crit_var = tk.StringVar(value="nombre")
    ttk.Combobox(search_bar, textvariable=crit_var, width=12, state="readonly", values=["nombre","dni"]).pack(side=tk.LEFT, padx=6)

    # tabla + scrolls
    yb = ttk.Scrollbar(right, orient="vertical")
    xb = ttk.Scrollbar(right, orient="horizontal")
    table = ttk.Treeview(right, columns=COLUMNS, show="headings", yscrollcommand=yb.set, xscrollcommand=xb.set)
    yb.config(command=table.yview); xb.config(command=table.xview)
    table.pack(side=tk.TOP, fill=tk.BOTH, expand=True); yb.pack(side=tk.RIGHT, fill=tk.Y); xb.pack(side=tk.BOTTOM, fill=tk.X)

    for c in COLUMNS:
        table.heading(c, text=HEADERS[c])
        table.column(c, width=WIDTHS.get(c,120), anchor="w", stretch=True)

    return right, table, q_var, crit_var

def cargar_desde_tabla(table, fields):
    sel = table.focus()
    if not sel: return
    data = table.item(sel,'values')
    # entries
    fields["nombre"].delete(0, tk.END); fields["nombre"].insert(0, data[1])
    fields["dni"].delete(0, tk.END); fields["dni"].insert(0, data[2])
    fields["edad"].delete(0, tk.END); fields["edad"].insert(0, data[3])
    fields["domicilio"].delete(0, tk.END); fields["domicilio"].insert(0, data[4])
    fields["obra_social"].delete(0, tk.END); fields["obra_social"].insert(0, data[5])
    fields["numero_beneficio"].delete(0, tk.END); fields["numero_beneficio"].insert(0, data[6])
    fields["telefono"].delete(0, tk.END); fields["telefono"].insert(0, data[7])
    fields["email"].delete(0, tk.END); fields["email"].insert(0, data[8])
    fields["motivo_consulta"].delete(0, tk.END); fields["motivo_consulta"].insert(0, data[14] or "")
    # texts
    fields["antecedentes_personales"].delete("1.0", tk.END); fields["antecedentes_personales"].insert(tk.END, data[9] or "")
    fields["antecedentes_familiares"].delete("1.0", tk.END); fields["antecedentes_familiares"].insert(tk.END, data[10] or "")
    fields["examen_fisico"].delete("1.0", tk.END); fields["examen_fisico"].insert(tk.END, data[11] or "")
    fields["diagnostico_presuntivo"].delete("1.0", tk.END); fields["diagnostico_presuntivo"].insert(tk.END, data[12] or "")
    fields["evolucion_seguimiento"].delete("1.0", tk.END); fields["evolucion_seguimiento"].insert(tk.END, data[13] or "")

def bind_context_menu(root, widgets):
    menu = tk.Menu(root, tearoff=0)
    def show_menu(e):
        w = e.widget; menu.delete(0,"end")
        if isinstance(w, (tk.Entry, ttk.Entry)):
            menu.add_command(label="Copiar", command=lambda: root.clipboard_clear() or root.clipboard_append(w.get()))
            menu.add_command(label="Pegar",  command=lambda: w.delete(0, tk.END) or w.insert(0, root.clipboard_get()))
            menu.tk_popup(e.x_root, e.y_root)
        elif isinstance(w, (tk.Text, scrolledtext.ScrolledText)):
            menu.add_command(label="Copiar", command=lambda: root.clipboard_clear() or root.clipboard_append(w.get("1.0", tk.END)))
            menu.add_command(label="Pegar",  command=lambda: w.delete("1.0", tk.END) or w.insert(tk.END, root.clipboard_get()))
            menu.tk_popup(e.x_root, e.y_root)
    for w in widgets: w.bind("<Button-3>", show_menu)
