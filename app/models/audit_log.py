import json
from datetime import datetime, timezone
from app.extensions import db

ACTIONS = (
    'DOCUMENT_CREATED', 'DOCUMENT_SENT', 'DOCUMENT_COMPLETED', 'DOCUMENT_CANCELLED',
    'SIGNING_LINK_OPENED', 'OTP_SENT', 'OTP_VERIFIED', 'OTP_FAILED',
    'SIGNATURE_SUBMITTED', 'TOKEN_EXPIRED', 'REQUEST_CANCELLED', 'REQUEST_RESENT',
    'VERIFICATION_CHECKED', 'DRIVE_UPLOADED', 'REMINDER_SENT',
)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True)
    signature_request_id = db.Column(db.Integer, db.ForeignKey('signature_requests.id', ondelete='SET NULL'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    actor_email = db.Column(db.String(255), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    _details = db.Column('details', db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    _geolocation = db.Column('geolocation', db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def details(self):
        return json.loads(self._details) if self._details else {}

    @details.setter
    def details(self, value):
        self._details = json.dumps(value, ensure_ascii=False) if value else None

    @property
    def geolocation(self):
        return json.loads(self._geolocation) if self._geolocation else {}

    @geolocation.setter
    def geolocation(self, value):
        self._geolocation = json.dumps(value, ensure_ascii=False) if value else None

    def __repr__(self) -> str:
        return f'<AuditLog {self.action} by {self.actor_email}>'
