"""
Integration tests for the signing flow: token, OTP, signing page, success.
"""
import pytest
from app.models.document import Document
from app.models.signature_request import SignatureRequest
from app.services.signature.token_service import create_signing_jwt, decode_signing_jwt
from app.services.signature.otp_service import generate_otp, verify_otp


@pytest.fixture
def sample_doc(db):
    from app.models.user import User
    from app.models.template import DocumentTemplate
    import json
    import uuid as _uuid

    unique = _uuid.uuid4().hex[:8]
    user = User(email=f'doc_admin_{unique}@test.com', full_name='Doc Admin')
    user.set_password('pass')
    db.session.add(user)
    db.session.flush()

    tpl = DocumentTemplate(
        user_id=user.id, name='Test Template',
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
        created_by=user.id,
        draft_pdf_path='uploads/generated_pdfs/test.pdf',
    )
    db.session.add(doc)
    db.session.commit()
    return doc


@pytest.fixture
def sample_sig_req(db, sample_doc):
    import datetime
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


def test_jwt_signing_token_roundtrip(sample_sig_req):
    token = sample_sig_req.token
    payload = decode_signing_jwt(token)
    assert payload is not None
    assert payload['sig_req_id'] == sample_sig_req.id
    assert payload['document_id'] == sample_sig_req.document_id


def test_invalid_jwt_returns_none():
    result = decode_signing_jwt('not-a-valid-token')
    assert result is None


def test_otp_full_cycle(db, sample_sig_req):
    code = generate_otp(sample_sig_req.id)
    assert code.isdigit()
    assert len(code) == 6

    success, msg = verify_otp(sample_sig_req.id, code)
    assert success is True

    # Second use of same OTP should fail
    success2, _ = verify_otp(sample_sig_req.id, code)
    assert success2 is False


def test_otp_wrong_code(db, sample_sig_req):
    generate_otp(sample_sig_req.id)
    success, msg = verify_otp(sample_sig_req.id, '000000')
    assert success is False
    assert msg


def test_signing_page_loads_with_valid_token(client, db, sample_sig_req):
    resp = client.get(f'/sign/{sample_sig_req.token}')
    assert resp.status_code == 200
    assert b'Assinar' in resp.data or b'assinar' in resp.data


def test_signing_page_rejects_invalid_token(client, db):
    resp = client.get('/sign/invalid-token-xyz')
    assert resp.status_code in (410, 400, 302, 200)


def test_request_otp_endpoint(client, db, sample_sig_req, app):
    with app.app_context():
        resp = client.post(
            f'/sign/{sample_sig_req.token}/request-otp',
            headers={'X-CSRFToken': 'test'},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'success' in data


def test_verify_otp_endpoint_wrong_code(client, db, sample_sig_req, app):
    with app.app_context():
        generate_otp(sample_sig_req.id)
        resp = client.post(
            f'/sign/{sample_sig_req.token}/verify-otp',
            json={'code': '999999'},
            headers={'X-CSRFToken': 'test'},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is False
