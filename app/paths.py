# paths.py
import os, sys

def get_paths():
    base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    paths = {
        "BASE_DIR": base,
        "DB_NAME": os.path.join(base, "historias_clinicas_v5.db"),
        "PDFS_DIR": os.path.join(base, "PDFs"),
        "IMAGES_DIR": os.path.join(base, "imagenes"),
        "LOGO_PATH": os.path.join(base, "imagenes", "logo.png"),
        "CLIENT_SECRETS": os.path.join(base, "client_secrets.json"),
        "TOKEN_FILE": os.path.join(base, "token.json"),
        "DRIVE_FOLDER_NAME": "Backups Consultorio Dra. Zulma Cabrera",
    }
    os.makedirs(paths["PDFS_DIR"], exist_ok=True)
    os.makedirs(paths["IMAGES_DIR"], exist_ok=True)
    return paths
