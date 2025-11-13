# app/__init__.py

__version__ = "0.1.0"  # cambia cuando liberes

# Re-exports (opcional): facilitan `from app import ...`
from .paths import get_paths
from .db import init_db
from .ui import (
    build_form, build_actions, build_table,
    bind_context_menu, cargar_desde_tabla, clear_form
)
from .actions import (
    refresh_table, apply_filter, guardar, actualizar, borrar,
    export_csv, generar_pdf_action, backup_now_action,
)
from .backup_drive import can_backup

# Controlá qué se exporta con from app import *
__all__ = [
    "__version__",
    "get_paths", "init_db",
    "build_form", "build_actions", "build_table",
    "bind_context_menu", "cargar_desde_tabla", "clear_form",
    "refresh_table", "apply_filter", "guardar", "actualizar", "borrar",
    "export_csv", "generar_pdf_action", "backup_now_action",
    "can_backup",
]
