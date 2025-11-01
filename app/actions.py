# actions.py
import tkinter as tk
from tkinter import messagebox, filedialog
import csv, datetime

from validators import validar_campos
from ui import clear_form
from pdf_utils import generar_pdf
from backup_drive import backup_now, can_backup

def refresh_table(table, cur):
    table.delete(*table.get_children())
    cur.execute("SELECT * FROM historias")
    for row in cur.fetchall():
        table.insert("", tk.END, values=row)

def apply_filter(table, cur, q: str, crit: str):
    table.delete(*table.get_children())
    if q:
        cur.execute(f"SELECT * FROM historias WHERE {crit} LIKE ?", (f"%{q}%",))
    else:
        cur.execute("SELECT * FROM historias")
    for row in cur.fetchall():
        table.insert("", tk.END, values=row)

def guardar(cur, conn, fields, on_done):
    from ui import get_form_data
    data = get_form_data(fields)
    ok, msg = validar_campos(data)
    if not ok:
        return messagebox.showwarning("Validación", msg)

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
    clear_form(fields); on_done(); messagebox.showinfo("Éxito","Historia clínica guardada")

def actualizar(cur, conn, table, fields, on_done):
    from ui import get_form_data
    sel = table.focus()
    if not sel:
        return messagebox.showwarning("Atención","Seleccioná una historia para actualizar")
    row_id = table.item(sel,'values')[0]
    data = get_form_data(fields)
    ok, msg = validar_campos(data)
    if not ok:
        return messagebox.showwarning("Validación", msg)
    ordered = (
        data["nombre"], data["dni"], data["edad"], data["domicilio"], data["obra_social"],
        data["numero_beneficio"], data["telefono"], data["email"],
        data["antecedentes_personales"], data["antecedentes_familiares"],
        data["examen_fisico"], data["diagnostico_presuntivo"],
        data["evolucion_seguimiento"], data["motivo_consulta"], row_id
    )
    cur.execute("""UPDATE historias SET
        nombre=?, dni=?, edad=?, domicilio=?, obra_social=?, numero_beneficio=?, telefono=?, email=?,
        antecedentes_personales=?, antecedentes_familiares=?, examen_fisico=?, diagnostico_presuntivo=?, evolucion_seguimiento=?, motivo_consulta=?
        WHERE id=?""", ordered)
    conn.commit()
    clear_form(fields); on_done(); messagebox.showinfo("Éxito","Historia clínica actualizada")

def borrar(cur, conn, table, on_done, fields):
    sel = table.focus()
    if not sel:
        return messagebox.showwarning("Atención","Seleccioná una historia para borrar")
    row_id = table.item(sel,'values')[0]
    if not messagebox.askyesno("Confirmar","¿Querés borrar esta historia clínica?"):
        return
    cur.execute("DELETE FROM historias WHERE id=?", (row_id,))
    conn.commit()
    clear_form(fields); on_done()

def export_csv(cur):
    path = filedialog.asksaveasfilename(
        title="Guardar CSV", defaultextension=".csv",
        initialfile=f"historias_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv",
        filetypes=[("CSV","*.csv")]
    )
    if not path: return
    cur.execute("SELECT * FROM historias"); rows = cur.fetchall()
    headers = [d[0] for d in cur.description]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";"); w.writerow(headers); w.writerows(rows)
    messagebox.showinfo("CSV", f"Se exportaron {len(rows)} filas a:\n{path}")

def generar_pdf_action(paths, table):
    sel = table.focus()
    if not sel:
        return messagebox.showwarning("Atención","Seleccioná una historia para generar PDF")
    out = generar_pdf(paths, table.item(sel,'values'))
    messagebox.showinfo("PDF", f"PDF guardado en:\n{out}")

def backup_now_action(paths):
    if not can_backup(paths):
        return messagebox.showwarning("Backup","Falta PyDrive2 o client_secrets.json")
    try:
        backup_now(paths)
        messagebox.showinfo("Backup","Copia de seguridad subida a Google Drive")
    except Exception as e:
        messagebox.showerror("Backup", f"Error: {e}")
