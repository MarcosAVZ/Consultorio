# backup_drive.py
import os, zipfile, datetime, time

try:
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
    PYDRIVE_AVAILABLE = True
except Exception:
    PYDRIVE_AVAILABLE = False

# PyDrive2 importada + client_secrets.json existe en la ruta que define paths.py
def can_backup(paths: dict) -> bool:
    
    return PYDRIVE_AVAILABLE and os.path.exists(paths["CLIENT_SECRETS"])

def backup_now(paths: dict):
    if not can_backup(paths):
        raise RuntimeError("No está disponible PyDrive2 o falta client_secrets.json")

    # Configurar GoogleAuth con backend 'file' y rutas explícitas
    gauth = GoogleAuth(settings={
        "client_config_backend": "file",
        "client_config_file": paths["CLIENT_SECRETS"],   # ruta absoluta al JSON
        "save_credentials": True,
        "save_credentials_backend": "file",
        "save_credentials_file": paths["TOKEN_FILE"],     # ruta absoluta al token
        # Pedimos alcance acotado: solo archivos creados por la app
        "oauth_scope": ["https://www.googleapis.com/auth/drive.file"],
        # Forzar refresh_token
        "oauth_request_params": {"access_type": "offline", "prompt": "consent"},
        # Si 8080 está ocupado, PyDrive2 probará también 8090
        "auth_host_port": [8080, 8090],
        "auth_local_webserver": True,
    })

    # Cargar credenciales previas si existen
    gauth.LoadCredentialsFile(paths["TOKEN_FILE"])
    
    if gauth.credentials is None:
        # Primera vez: abre el navegador
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresca usando refresh_token del token guardado
        gauth.Refresh()
    else:
        gauth.Authorize()

    # Guardar/actualizar token
    gauth.SaveCredentialsFile(paths["TOKEN_FILE"])

    # Verificación opcional: asegurar que tenemos refresh_token
    if not getattr(gauth.credentials, "refresh_token", None):
        raise RuntimeError("No refresh_token disponible. Revoque el acceso y autorice nuevamente con 'offline'.")

    drive = GoogleDrive(gauth)

    # Crear ZIP de la BD
    zip_name = f"Backup_{datetime.datetime.now():%Y%m%d_%H%M%S}.zip"
    zip_path = os.path.join(paths["BASE_DIR"], zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(paths["DB_NAME"], arcname=os.path.basename(paths["DB_NAME"]))

    
    q = "title='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false".format(
        name=paths["DRIVE_FOLDER_NAME"]
    )
    flist = drive.ListFile({'q': q}).GetList()
    if flist:
        folder_id = flist[0]['id']
    else:
        folder = drive.CreateFile({
            'title': paths['DRIVE_FOLDER_NAME'],
            'mimeType': 'application/vnd.google-apps.folder'
        })
        folder.Upload()
        folder_id = folder['id']

    # Subir el ZIP
    f = drive.CreateFile({'title': zip_name, 'parents': [{'id': folder_id}]})
    try:
        f.SetContentFile(zip_path)
        f.Upload()
    finally:
        
        try:
            if hasattr(f, "content") and hasattr(f.content, "close"):
                f.content.close()  
        except Exception:
            pass

    # Borrar ZIP local
    for _ in range(5):
        try:
            os.remove(zip_path)
            break
        except PermissionError:
            time.sleep(0.5)
