import json
from datetime import datetime, timezone
from app.extensions import db


class DocumentTemplate(db.Model):
    __tablename__ = 'document_templates'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    html_file_path = db.Column(db.String(500), nullable=False)
    _variables_schema = db.Column('variables_schema', db.Text, nullable=False, default='[]')
    sheet_connection_id = db.Column(db.Integer, db.ForeignKey('sheet_connections.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    owner = db.relationship('User', backref='document_templates')
    default_sheet = db.relationship('SheetConnection', backref='templates')

    @property
    def variables_schema(self):
        return json.loads(self._variables_schema)

    @variables_schema.setter
    def variables_schema(self, value):
        self._variables_schema = json.dumps(value, ensure_ascii=False)

    def __repr__(self) -> str:
        return f'<DocumentTemplate {self.name}>'
