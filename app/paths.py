# paths.py
import os, sys

APP_NAME    = "Consultorio"
DB_FILENAME = "historias_clinicas_v5.db"

def _user_data_dir() -> str:
    if sys.platform.startswith("win"):
        root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(root, APP_NAME)
    elif sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~/Library/Application Support"), APP_NAME)
    else:
        return os.path.join(os.path.expanduser("~/.local/share"), APP_NAME)

def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_paths():
    env_dir = os.environ.get("CONSULTORIO_DATA_DIR")
    frozen  = getattr(sys, "frozen", False)

    # 1) Raíz de datos
    if env_dir:
        base_dir = os.path.abspath(env_dir)
    elif frozen:
        base_dir = _user_data_dir()               # p.ej. %LOCALAPPDATA%\Consultorio
    else:
        base_dir = os.path.join(_repo_root(), "data")

    # 2) Subcarpetas: SOLO la BD va a data/db/
    db_dir     = os.path.join(base_dir, "db")
    pdfs_dir   = os.path.join(base_dir, "PDFs")
    images_dir = os.path.join(base_dir, "imagenes")

    # 3) Rutas finales
    db_path     = os.path.join(db_dir, DB_FILENAME)
    logo_path   = os.path.join(images_dir, "logo.png")
    client_json = os.path.join(base_dir, "client_secrets.json")
    token_file  = os.path.join(base_dir, "token.json")

    # 4) Crear carpetas
    os.makedirs(db_dir, exist_ok=True)
    os.makedirs(pdfs_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    # 5) Migración: mover BD si quedó en ubicaciones antiguas
    #    - data/historias_clinicas_v5.db  (raíz de data)
    #    - carpeta junto al ejecutable o junto a este archivo
    legacy_candidates = []

    # raíz de data (versión previa)
    legacy_candidates.append(os.path.join(base_dir, DB_FILENAME))

    # junto al exe o a este archivo
    old_base = os.path.dirname(sys.executable) if frozen else os.path.dirname(os.path.abspath(__file__))
    legacy_candidates.append(os.path.join(old_base, DB_FILENAME))

    for old_db in legacy_candidates:
        if os.path.exists(old_db) and not os.path.samefile(old_db, db_path) and not os.path.exists(db_path):
            try:
                os.replace(old_db, db_path)
                break
            except Exception:
                pass  # si no puede mover, no rompemos la ejecución

    return {
        "BASE_DIR": base_dir,
        "DB_DIR": db_dir,
        "DB_NAME": db_path,        # <- usa esto en init_db()
        "PDFS_DIR": pdfs_dir,
        "IMAGES_DIR": images_dir,
        "LOGO_PATH": logo_path,
        "CLIENT_SECRETS": client_json,
        "TOKEN_FILE": token_file,
        "DRIVE_FOLDER_NAME": "Backups Consultorio Dra. Zulma Cabrera",
    }
