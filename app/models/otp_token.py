from datetime import datetime, timezone
from app.extensions import db


class OtpToken(db.Model):
    __tablename__ = 'otp_tokens'

    id = db.Column(db.Integer, primary_key=True)
    signature_request_id = db.Column(db.Integer,
                                     db.ForeignKey('signature_requests.id'), nullable=False)
    code_hash = db.Column(db.String(64), nullable=False)  # SHA-256, never plaintext
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    used_at = db.Column(db.DateTime, nullable=True)

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)

    def __repr__(self) -> str:
        return f'<OtpToken sig_req={self.signature_request_id} used={self.is_used}>'
