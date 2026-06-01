import json
from cryptography.fernet import Fernet
from flask import current_app
import gspread
from google.oauth2.service_account import Credentials


_SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]


def _fernet() -> Fernet:
    key = current_app.config.get('CREDENTIALS_ENCRYPTION_KEY', '')
    if not key:
        raise ValueError('CREDENTIALS_ENCRYPTION_KEY not configured')
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_credentials(json_str: str) -> str:
    return _fernet().encrypt(json_str.encode()).decode()


def decrypt_credentials(encrypted: str) -> str:
    return _fernet().decrypt(encrypted.encode()).decode()


def get_worksheet(sheet_connection) -> gspread.Worksheet:
    decrypted = decrypt_credentials(sheet_connection.service_account_json)
    creds_dict = json.loads(decrypted)
    creds = Credentials.from_service_account_info(creds_dict, scopes=_SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_connection.spreadsheet_id)
    return spreadsheet.worksheet(sheet_connection.sheet_tab_name)
