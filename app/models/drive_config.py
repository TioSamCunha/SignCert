from datetime import datetime, timezone
from app.extensions import db


class DriveConfig(db.Model):
    __tablename__ = 'drive_configs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    display_name = db.Column(db.String(255), nullable=False, default='Google Drive')
    service_account_json = db.Column(db.Text, nullable=False)  # Fernet encrypted
    folder_id = db.Column(db.String(255), nullable=True)  # ID da pasta destino
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    owner = db.relationship('User', backref='drive_configs')

    def __repr__(self) -> str:
        return f'<DriveConfig {self.display_name}>'
