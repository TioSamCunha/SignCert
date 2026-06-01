import uuid
from datetime import datetime, timezone
from app.extensions import db

SIG_STATUS = ('pending', 'link_opened', 'otp_sent', 'otp_verified', 'signed', 'expired', 'cancelled')
SIG_METHODS = ('email_otp', 'sms_otp', 'digital_cert', 'simple')


class SignatureRequest(db.Model):
    __tablename__ = 'signature_requests'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), nullable=False, unique=True,
                     default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    signing_order = db.Column(db.Integer, default=1)
    method = db.Column(db.String(20), default='email_otp', nullable=False)

    signatory_name = db.Column(db.String(255), nullable=False)
    signatory_email = db.Column(db.String(255), nullable=False)
    signatory_cpf = db.Column(db.String(14), nullable=True)
    signatory_phone = db.Column(db.String(20), nullable=True)

    token = db.Column(db.String(512), nullable=True, unique=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='pending', nullable=False)

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    geolocation_country = db.Column(db.String(100), nullable=True)
    geolocation_region = db.Column(db.String(100), nullable=True)
    geolocation_city = db.Column(db.String(100), nullable=True)
    geolocation_lat = db.Column(db.Numeric(10, 7), nullable=True)
    geolocation_lon = db.Column(db.Numeric(10, 7), nullable=True)

    email_sent_at = db.Column(db.DateTime, nullable=True)
    link_opened_at = db.Column(db.DateTime, nullable=True)
    otp_sent_at = db.Column(db.DateTime, nullable=True)
    otp_verified_at = db.Column(db.DateTime, nullable=True)
    signed_at = db.Column(db.DateTime, nullable=True)

    signature_image_path = db.Column(db.String(500), nullable=True)
    signature_type = db.Column(db.String(20), nullable=True)
    document_hash_at_signing = db.Column(db.String(64), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    creator = db.relationship('User', backref='signature_requests')
    otp_tokens = db.relationship('OtpToken', backref='signature_request',
                                 cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<SignatureRequest {self.signatory_email} [{self.status}]>'
