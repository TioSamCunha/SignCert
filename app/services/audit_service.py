from datetime import datetime, timezone
from app.extensions import db
from app.models.audit_log import AuditLog


def log(action: str, *, document_id=None, signature_request_id=None,
        user_id=None, actor_email='sistema', details=None,
        ip=None, user_agent=None, geo=None) -> AuditLog:
    entry = AuditLog(
        document_id=document_id,
        signature_request_id=signature_request_id,
        user_id=user_id,
        actor_email=actor_email,
        action=action,
        ip_address=ip,
        user_agent=user_agent,
        timestamp=datetime.now(timezone.utc),
    )
    if details:
        entry.details = details
    if geo:
        entry.geolocation = geo
    db.session.add(entry)
    db.session.commit()
    return entry


def get_document_trail(document_id: int):
    return (AuditLog.query
            .filter_by(document_id=document_id)
            .order_by(AuditLog.timestamp.asc())
            .all())


def get_request_trail(signature_request_id: int):
    return (AuditLog.query
            .filter_by(signature_request_id=signature_request_id)
            .order_by(AuditLog.timestamp.asc())
            .all())
