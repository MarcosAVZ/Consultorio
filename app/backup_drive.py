# backup_drive.py
import os, zipfile, datetime

try:
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
    PYDRIVE_AVAILABLE = True
except Exception:
    PYDRIVE_AVAILABLE = False

def can_backup(paths: dict) -> bool:
    return PYDRIVE_AVAILABLE and os.path.exists(paths["CLIENT_SECRETS"])

def backup_now(paths: dict):
    if not can_backup(paths):
        raise RuntimeError("No está disponible PyDrive2 o falta client_secrets.json")

    gauth = GoogleAuth()
    gauth.LoadClientConfigFile(paths["CLIENT_SECRETS"])
    
    gauth.LoadCredentialsFile(paths["TOKEN_FILE"])
    
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile(paths["TOKEN_FILE"])

    drive = GoogleDrive(gauth)
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
