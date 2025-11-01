# db.py
import sqlite3

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS historias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        dni TEXT,
        edad INTEGER,
        domicilio TEXT,
        obra_social TEXT,
        numero_beneficio TEXT,
        telefono TEXT,
        email TEXT,
        antecedentes_personales TEXT,
        antecedentes_familiares TEXT,
        examen_fisico TEXT,
        diagnostico_presuntivo TEXT,
        evolucion_seguimiento TEXT,
        motivo_consulta TEXT
    )
    """)
    conn.commit()
    return conn, cur
