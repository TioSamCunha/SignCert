import uuid
from datetime import datetime, timezone, timedelta
import jwt
from flask import current_app


def create_signing_jwt(signature_request_id: int, document_id: int,
                       email: str, expires_hours: int = None) -> str:
    if expires_hours is None:
        expires_hours = current_app.config.get('SIGNING_TOKEN_EXPIRES_HOURS', 72)
    now = datetime.now(timezone.utc)
    payload = {
        'sig_req_id': signature_request_id,
        'document_id': document_id,
        'email': email,
        'iat': now,
        'exp': now + timedelta(hours=expires_hours),
        'jti': str(uuid.uuid4()),
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def decode_signing_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, current_app.config['SECRET_KEY'],
                          algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
