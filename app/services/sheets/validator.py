import json
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app
import gspread
from google.oauth2.service_account import Credentials

_SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets',
]


def validate_connection(spreadsheet_id: str, tab_name: str, credentials_json: str) -> tuple[bool, str]:
    try:
        creds_dict = json.loads(credentials_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=_SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(spreadsheet_id)
        spreadsheet.worksheet(tab_name)
        return True, 'Conexão bem-sucedida'
    except gspread.SpreadsheetNotFound:
        return False, 'Planilha não encontrada. Verifique o ID e as permissões da conta de serviço.'
    except gspread.WorksheetNotFound:
        return False, f'Aba "{tab_name}" não encontrada na planilha.'
    except Exception as e:
        return False, f'Erro: {str(e)}'


def validate_fernet_key(key: str) -> bool:
    try:
        Fernet(key.encode())
        return True
    except Exception:
        return False
