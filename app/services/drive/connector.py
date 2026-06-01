import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from app.services.sheets.connector import decrypt_credentials

_SCOPES = ['https://www.googleapis.com/auth/drive']


def get_drive_service(drive_config):
    decrypted = decrypt_credentials(drive_config.service_account_json)
    creds_dict = json.loads(decrypted)
    creds = Credentials.from_service_account_info(creds_dict, scopes=_SCOPES)
    return build('drive', 'v3', credentials=creds)


def check_drive_connection(credentials_json: str, folder_id: str = None) -> tuple[bool, str]:
    try:
        creds = Credentials.from_service_account_info(
            json.loads(credentials_json), scopes=_SCOPES)
        service = build('drive', 'v3', credentials=creds)
        if folder_id:
            service.files().get(fileId=folder_id, fields='id,name').execute()
        else:
            service.files().list(pageSize=1).execute()
        return True, 'Conexão bem-sucedida'
    except Exception as e:
        return False, f'Erro: {str(e)}'


def create_folder(service, name: str, parent_id: str = None) -> str:
    metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id:
        metadata['parents'] = [parent_id]
    f = service.files().create(body=metadata, fields='id').execute()
    return f['id']
