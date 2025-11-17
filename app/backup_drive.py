# backup_drive.py
import os, zipfile, datetime, time
from paths import load_config, save_config


try:
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
    PYDRIVE_AVAILABLE = True
except Exception:
    PYDRIVE_AVAILABLE = False

def _marcar_ultimo_backup(paths: dict):
    base_dir = paths["BASE_DIR"]
    cfg = load_config(base_dir)
    cfg["last_backup"] = datetime.date.today().isoformat()
    save_config(base_dir, cfg)
    print("[DEBUG] Último backup registrado en config.json")

# PyDrive2 importada + client_secrets.json existe en la ruta que define paths.py
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
            gauth.flow.params.update({'access_type': 'offline'})
            gauth.flow.params.pop('approval_prompt', None)
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

    # Verificación opcional: asegurar que tenemos refresh_token
    if not getattr(gauth.credentials, "refresh_token", None):
        raise RuntimeError("No refresh_token disponible. Revoque el acceso y autorice nuevamente con 'offline'.")

    drive = GoogleDrive(gauth)
    

# Lógica zip (igual que antes)
    zip_name = f"Backup_{datetime.datetime.now():%Y%m%d_%H%M%S}.zip"
    zip_path = os.path.join(paths["BASE_DIR"], zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(paths["DB_NAME"], arcname=os.path.basename(paths["DB_NAME"]))
        
    q = f"title='{paths['DRIVE_FOLDER_NAME']}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
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


    # Subida al Drive
    f = drive.CreateFile({'title': zip_name, 'parents':[{'id': folder_id}]})
    f.SetContentFile(zip_path)
    f.Upload()
    print("[DEBUG] Archivo subido a Drive:", zip_path)
    _marcar_ultimo_backup(paths)
    # Asegurar que todos los handles de archivo están cerrados → liberamos manualmente
    try:
        del f  # eliminar referencia
    except NameError:
        pass

    # Intentar eliminar el zip local
    try:
        os.remove(zip_path)
        print("[DEBUG] Archivo zip local eliminado:", zip_path)
    except Exception as ex:
        print("[DEBUG] Error al borrar localmente el zip:", zip_path, ex)
        

def maybe_auto_backup(paths: dict, dias: int = 7):
    
    #
    
    if not can_backup(paths):
        print("[DEBUG] No se puede hacer backup (falta PyDrive o client_secrets.json)")
        return

    today = datetime.date.today()
    base_dir = paths["BASE_DIR"]
    cfg = load_config(base_dir)

    last_str = cfg.get("last_backup")

    if not last_str:
        # Nunca se hizo backup → hacemos el primero ahora
        print("[DEBUG] No hay registro de backup previo, ejecutando primero backup...")
        backup_now(paths)
        return

    try:
        last_date = datetime.date.fromisoformat(last_str)
    except Exception:
        # Si el dato está corrupto, forzamos backup
        print("[DEBUG] Fecha de último backup inválida, forzando backup...")
        backup_now(paths)
        return

    diff = (today - last_date).days
    print(f"[DEBUG] Días desde el último backup: {diff}")

    if diff >= dias:
        print(f"[DEBUG] Pasaron {diff} días, toca backup automático")
        backup_now(paths)
    else:
        print(f"[DEBUG] Aún no toca backup (faltan {dias - diff} días)")
