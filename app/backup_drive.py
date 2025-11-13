# backup_drive.py
import os, zipfile, datetime

try:
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
    PYDRIVE_AVAILABLE = True
except Exception:
    PYDRIVE_AVAILABLE = False

def can_backup(paths: dict) -> bool:
    print("[DEBUG] revisando si puede hacer backup")
    return PYDRIVE_AVAILABLE and os.path.exists(paths["CLIENT_SECRETS"])

def backup_now(paths: dict):
    if not can_backup(paths):
        print("[DEBUG] client_secrets:", paths.get("CLIENT_SECRETS"))
        print("[DEBUG] token_file:", paths.get("TOKEN_FILE"))
        print("[DEBUG] base_dir:", paths.get("BASE_DIR"))
        raise RuntimeError("No está disponible PyDrive2 o falta client_secrets.json")
    gauth = GoogleAuth()
    # configuración: offline + consent
    gauth.settings['get_refresh_token'] = True
    gauth.settings['oauth_scope'] = ['https://www.googleapis.com/auth/drive']
    gauth.settings['client_config_file'] = paths["CLIENT_SECRETS"]

    token_file = paths["TOKEN_FILE"]

    # cargar si existe
    if os.path.exists(token_file):
        gauth.LoadCredentialsFile(token_file)

    try:
        if gauth.credentials is None:
            print("[DEBUG] No hay credenciales, iniciando autorizar de nuevo")
            gauth.GetFlow()
            gauth.flow.params.update({'access_type': 'offline', 'prompt': 'consent'})
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            print("[DEBUG] Token expirado, refrescando")
            gauth.Refresh()
        else:
            print("[DEBUG] Credenciales válidas, autorizando")
            gauth.Authorize()

        # Guardar credenciales nuevas
        gauth.SaveCredentialsFile(token_file)
        print("[DEBUG] Credenciales guardadas en:", token_file)

    except Exception as ex:
        print("[DEBUG] Falló autenticación/re-autorización:", ex)
        # eliminar token viejo si existe
        if os.path.exists(token_file):
            os.remove(token_file)
            print("[DEBUG] Archivo token eliminado:", token_file)
        # intentar de nuevo autorización completa
        gauth.LocalWebserverAuth()
        gauth.SaveCredentialsFile(token_file)
        print("[DEBUG] Re-autorización completada, credenciales guardadas")

    drive = GoogleDrive(gauth)
    
    #logica zip
    zip_name = f"Backup_{datetime.datetime.now():%Y%m%d_%H%M%S}.zip"
    zip_path = os.path.join(paths["BASE_DIR"], zip_name)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(paths["DB_NAME"], arcname=os.path.basename(paths["DB_NAME"]))

    q = f"title='{paths['DRIVE_FOLDER_NAME']}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    flist = drive.ListFile({'q': q}).GetList()
    if flist:
        folder_id = flist[0]['id']
    else:
        folder = drive.CreateFile({'title': paths['DRIVE_FOLDER_NAME'], 'mimeType': 'application/vnd.google-apps.folder'})
        folder.Upload()
        folder_id = folder['id']

    f = drive.CreateFile({'title': zip_name, 'parents':[{'id': folder_id}]})
    f.SetContentFile(zip_path); f.Upload()
    os.remove(zip_path)
