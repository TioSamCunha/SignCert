import hashlib
import hmac
import secrets
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.extensions import db
from app.models.otp_token import OtpToken


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def generate_otp(signature_request_id: int) -> str:
    invalidate_existing(signature_request_id)
    code = str(secrets.randbelow(1000000)).zfill(6)
    expires_minutes = current_app.config.get('OTP_EXPIRES_MINUTES', 10)
    token = OtpToken(
        signature_request_id=signature_request_id,
        code_hash=_hash_code(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
    )
    db.session.add(token)
    db.session.commit()
    return code


def verify_otp(signature_request_id: int, code: str) -> tuple[bool, str]:
    max_attempts = current_app.config.get('OTP_MAX_ATTEMPTS', 3)
    token = (OtpToken.query
             .filter_by(signature_request_id=signature_request_id, is_used=False)
             .order_by(OtpToken.created_at.desc())
             .first())
    if not token:
        return False, 'Código não encontrado. Solicite um novo.'
    if token.is_expired():
        return False, 'Código expirado. Solicite um novo.'
    if token.attempts >= max_attempts:
        return False, 'Muitas tentativas. Solicite um novo código.'
    token.attempts += 1
    db.session.commit()
    expected = _hash_code(code)
    if not hmac.compare_digest(expected, token.code_hash):
        return False, 'Código inválido.'
    token.is_used = True
    token.used_at = datetime.now(timezone.utc)
    db.session.commit()
    return True, 'OK'


def invalidate_existing(signature_request_id: int) -> None:
    (OtpToken.query
     .filter_by(signature_request_id=signature_request_id, is_used=False)
     .update({'is_used': True}))
    db.session.commit()
