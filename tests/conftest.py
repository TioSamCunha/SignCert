import json
import uuid as _uuid
import datetime
import pytest

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()


@pytest.fixture(scope='function')
def admin_user(db):
    from app.models.user import User
    unique = _uuid.uuid4().hex[:8]
    u = User(email=f'admin_{unique}@test.com', full_name='Admin Test', is_superadmin=True)
    u.set_password('password123')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture(scope='function')
def sample_doc(db, admin_user):
    from app.models.document import Document
    from app.models.template import DocumentTemplate

    tpl = DocumentTemplate(
        user_id=admin_user.id,
        name='Test Template',
        html_file_path='sample.html',
        variables_schema=json.dumps([]),
    )
    db.session.add(tpl)
    db.session.flush()

    doc = Document(
        template_id=tpl.id,
        title='Contrato de Teste',
        rendered_variables=json.dumps({}),
        sheet_snapshot=json.dumps({}),
        status='pending_signatures',
        created_by=admin_user.id,
        draft_pdf_path='uploads/generated_pdfs/test.pdf',
    )
    db.session.add(doc)
    db.session.commit()
    return doc


@pytest.fixture(scope='function')
def sample_sig_req(db, sample_doc):
    from app.models.signature_request import SignatureRequest
    from app.services.signature.token_service import create_signing_jwt

    sig_req = SignatureRequest(
        document_id=sample_doc.id,
        signatory_name='João Silva',
        signatory_email='joao@example.com',
        method='email_otp',
        status='pending',
        token_expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=72),
        created_by=sample_doc.created_by,
    )
    db.session.add(sig_req)
    db.session.flush()

    token = create_signing_jwt(sig_req.id, sample_doc.id, sig_req.signatory_email)
    sig_req.token = token
    db.session.commit()
    return sig_req


@pytest.fixture(scope='function')
def logged_in_client(client, admin_user):
    """Returns a test client already authenticated as admin."""
    client.post('/auth/login', data={
        'email': admin_user.email,
        'password': 'password123',
    })
    return client
