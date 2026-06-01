import re
from datetime import datetime
import pytz


def format_cpf(cpf: str) -> str:
    digits = re.sub(r'\D', '', cpf or '')
    if len(digits) == 11:
        return f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}'
    return cpf


def format_cnpj(cnpj: str) -> str:
    digits = re.sub(r'\D', '', cnpj or '')
    if len(digits) == 14:
        return f'{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}'
    return cnpj


def to_brasilia(dt: datetime, fmt: str = '%d/%m/%Y %H:%M:%S') -> str:
    if dt is None:
        return '-'
    tz = pytz.timezone('America/Sao_Paulo')
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(tz).strftime(fmt)


def mask_email(email: str) -> str:
    if not email or '@' not in email:
        return email
    user, domain = email.split('@', 1)
    masked = user[:2] + '***' if len(user) > 2 else '***'
    return f'{masked}@{domain}'
