# Consultorio Gerontológico Integral — Historias Clínicas (Tkinter + SQLite)

Aplicación de escritorio para gestionar **historias clínicas**. Permite **crear, editar, buscar, eliminar**, **exportar a PDF/CSV** y realizar **backups opcionales** en Google Drive (PyDrive2).

---

## Arquitectura del paquete `app/`

> Todo el código fuente vive en `app/` (paquete Python). Ejecutá la app desde la **raíz** del proyecto con:
>
> ```bash
> python -m app.main
> ```

### `app/__init__.py`
- **Propósito:** marca `app/` como paquete importable.
- **Contenido típico:** puede estar vacío o exponer una API mínima (`__version__`, re-exports).
- **Buenas prácticas:** evitar lógica al importar (no abrir DB ni crear ventanas aquí).

---

### `app/main.py`
**Rol:** punto de entrada de la aplicación.

**Responsabilidades:**
- Resuelve rutas con `paths.get_paths()`.
- Inicializa la base con `db.init_db()`.
- Construye la interfaz (formulario, acciones y tabla) usando `ui.build_*`.
- Conecta handlers de botones con funciones de `actions`.
- Carga datos iniciales y arranca el loop de Tkinter (`root.mainloop()`).

**Depende de:** `paths`, `db`, `ui`, `actions`, `backup_drive` (para habilitar/deshabilitar backup).

---

### `app/ui.py`
**Rol:** capa de **presentación** (Tkinter). Crea widgets y utilidades visuales.

**Funciones clave:**
- `build_form(root)` → crea el formulario y devuelve los widgets.
- `build_actions(root, handlers)` → crea la botonera y vincula callbacks.
- `build_table(root)` → buscador + `Treeview` + scrollbars.
- `cargar_desde_tabla(table, fields)` → copia una fila seleccionada al formulario.
- `bind_context_menu(root, widgets)` → menú Copiar/Pegar.
- `clear_form(fields)` → limpia todos los campos.

**No hace:** validación, acceso a datos ni lógica de negocio.

---

### `app/actions.py`
**Rol:** **lógica de aplicación**. Orquesta UI + DB + utilidades.

**Funciones clave:**
- `refresh_table(table, cur)` y `apply_filter(table, cur, q, crit)` → rellenar/filtrar la tabla.
- `guardar(cur, conn, fields, on_done)` → `INSERT` (con validación).
- `actualizar(cur, conn, table, fields, on_done)` → `UPDATE`.
- `borrar(cur, conn, table, on_done, fields)` → `DELETE`.
- `export_csv(cur)` → exporta toda la tabla a CSV.
- `generar_pdf_action(paths, table)` → obtiene la fila y llama a `pdf_utils.generar_pdf()`.
- `backup_now_action(paths)` → dispara `backup_drive.backup_now()` si está disponible.

**Depende de:** `validators`, `pdf_utils`, `backup_drive`, `sqlite3`, y widgets de `ui`.

---

### `app/db.py`
**Rol:** **acceso a datos** (SQLite).

**Funciones clave:**
- `init_db(db_path) -> (conn, cursor)` → abre la DB y garantiza la tabla `historias`:

Campos de `historias`:


**Depende de:** `sqlite3`.

---

### `app/validators.py`
**Rol:** **validación de negocio**.

**Función clave:**
- `validar_campos(data: dict) -> tuple[bool, str]`
  - Reglas: nombre y DNI obligatorios; DNI numérico (≥7 dígitos); edad 0–120; email/teléfono con formato válido.

**Depende de:** `re`.

---

### `app/pdf_utils.py`
**Rol:** **generación de PDF** con FPDF.

**Función clave:**
- `generar_pdf(paths, row_values) -> str`
  - Crea un A4 por historia, incluye logo si existe `paths["LOGO_PATH"]`.
  - Devuelve la ruta del PDF en `data/pdfs/`.

**Depende de:** `fpdf2` (y opcionalmente `Pillow`), `os/pathlib`.

---

### `app/backup_drive.py` *(opcional)*
**Rol:** **copia de seguridad** en Google Drive (PyDrive2).

**Funciones clave:**
- `can_backup(paths) -> bool` → verifica PyDrive2 + `client_secrets.json`.
- `backup_now(paths)` → comprime la DB en `.zip` y la sube a Drive (crea carpeta si falta).

**Depende de:** `pydrive2`, `zipfile`, `datetime`, `os/pathlib`.

---

### `app/paths.py`
**Rol:** **resolución de rutas** robustas (funciona como script o EXE).

**Función clave:**
- `get_paths() -> dict` con:
  - `BASE_DIR` (raíz del proyecto o carpeta del ejecutable),
  - `DB_NAME` (`data/db/historias_clinicas.db`),
  - `PDFS_DIR`, `IMAGES_DIR`, `LOGO_PATH`,
  - `CLIENT_SECRETS`, `TOKEN_FILE`,
  - `BACKUPS_DIR`, `DRIVE_FOLDER_NAME`.

También crea directorios necesarios si no existen.

**Depende de:** `pathlib`, `sys`.

---

### Diagrama (flujo simplificado)

sql
````mermaid
flowchart LR
  %% Mapa de módulos del paquete `app/`

  subgraph APP["Paquete app/"]
    A["main.py\nPunto de entrada"]
    P["paths.py\nRutas y directorios"]
    D["db.py\nSQLite: conn, cursor"]
    U["ui.py\nWidgets Tk / Layout"]
    ACT["actions.py\nCRUD · CSV · PDF · Backup"]
    PDF["pdf_utils.py\nGeneración de PDF"]
    BKP["backup_drive.py\nBackup Google Drive"]
  end

  %% Flujo principal
  A --> P
  A --> D
  A --> U
  A --> ACT

  %% Dependencias secundarias
  ACT --> PDF
  ACT --> BKP

  %% Usuario final
  USER["Usuario final"]
  U --> USER
````
---

## ✨ Características

- **CRUD** completo de historias clínicas (Tkinter).
- **Filtro** de búsqueda por **nombre** o **DNI**.
- **Generación de PDF** por historia (con **logo** opcional).
- **Exportación CSV** de todos los registros.
- **SQLite** embebido (sin servidores).
- **Backup opcional** a Google Drive (OAuth).
- Menú contextual **Copiar/Pegar** en entradas y textos.

---

## 🧱 Estructura de carpetas

```bash
CProyectoConsultorio/
├─ app/                         # Código fuente (paquete Python)
│  ├─ __init__.py
│  ├─ main.py                   # Entry point: arma la ventana y orquesta todo
│  ├─ ui.py                     # Construcción de UI (formulario/tabla/menú)
│  ├─ actions.py                # Lógica CRUD + exportaciones + handlers
│  ├─ db.py                     # Inicialización/ conexión a SQLite
│  ├─ validators.py             # Validaciones de campos
│  ├─ pdf_utils.py              # Generación de PDFs (fpdf2, Pillow)
│  ├─ backup_drive.py           # Backup con PyDrive2 (opcional)
│  └─ paths.py                  # Rutas robustas (script o ejecutable)
│
├─ data/                        # Datos en runtime
│  ├─ db/
│  │  └─ historias_clinicas.db  # SQLite (se crea si no existe)
│  ├─ pdfs/                     # PDFs generados
│  └─ imagenes/                 # logo.png (opcional)
│   
│     
│    
│
├─ dist/                        # Ejecutables generados (PyInstaller)
├─ build/                       # Temporales de PyInstaller
├─ .vscode/                     # Configuración de VS Code (opcional)
├─ .gitignore
├─ .gitattributes
└─ requirements.txt

```

## Iniciar Aplicacion

### 1) Clonar el repositorio
```bash
git clone https://github.com/MarcosAVZ/Consultorio.git
```
### 2) Crear y activar el entorno virtual
#### --- Windows (PowerShell) ---
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
### 3) Instalar dependencias

```bash
python -m pip install --upgrade pip
cd consultorio
pip install -r requirements.txt
```
### 4) Ejecutar la aplicación (desde la raíz del repo)
```bash
python cd app
python main.py
