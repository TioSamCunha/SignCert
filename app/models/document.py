import json
import uuid
from datetime import datetime, timezone
from app.extensions import db

DOC_STATUS = ('draft', 'pending_signatures', 'partially_signed', 'completed', 'cancelled')


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), nullable=False, unique=True,
                     default=lambda: str(uuid.uuid4()))
    template_id = db.Column(db.Integer, db.ForeignKey('document_templates.id'), nullable=False)
    sheet_connection_id = db.Column(db.Integer, db.ForeignKey('sheet_connections.id'), nullable=True)
    sheet_row_index = db.Column(db.Integer, nullable=True)
    _sheet_snapshot = db.Column('sheet_snapshot', db.Text, nullable=False, default='{}')
    _rendered_variables = db.Column('rendered_variables', db.Text, nullable=False, default='{}')
    draft_pdf_path = db.Column(db.String(500), nullable=True)
    pdf_path = db.Column(db.String(500), nullable=True)
    sha256_hash = db.Column(db.String(64), nullable=True)
    sha256_draft_hash = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(50), default='draft', nullable=False)
    title = db.Column(db.String(500), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)
    drive_file_id = db.Column(db.String(255), nullable=True)
    drive_file_url = db.Column(db.String(500), nullable=True)

    template = db.relationship('DocumentTemplate', backref='documents')
    sheet = db.relationship('SheetConnection', backref='documents')
    creator = db.relationship('User', backref='documents')
    signature_requests = db.relationship('SignatureRequest', backref='document',
                                         cascade='all, delete-orphan', lazy='dynamic')

    @property
    def sheet_snapshot(self):
        return json.loads(self._sheet_snapshot)

    @sheet_snapshot.setter
    def sheet_snapshot(self, value):
        self._sheet_snapshot = json.dumps(value, ensure_ascii=False)

    @property
    def rendered_variables(self):
        return json.loads(self._rendered_variables)

    @rendered_variables.setter
    def rendered_variables(self, value):
        self._rendered_variables = json.dumps(value, ensure_ascii=False)

    def __repr__(self) -> str:
        return f'<Document {self.title} [{self.status}]>'
