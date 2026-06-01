from datetime import datetime, timezone
from app.extensions import db


class SheetConnection(db.Model):
    __tablename__ = 'sheet_connections'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    spreadsheet_id = db.Column(db.String(255), nullable=False)
    sheet_tab_name = db.Column(db.String(255), default='Sheet1')
    service_account_json = db.Column(db.Text, nullable=False)  # Fernet encrypted
    header_row = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    owner = db.relationship('User', backref='sheet_connections')

    def __repr__(self) -> str:
        return f'<SheetConnection {self.display_name}>'
