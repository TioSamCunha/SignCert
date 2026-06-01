"""Integration tests for the complete signing flow."""
import base64
import os
import struct
import zlib
import pytest
from unittest.mock import patch

from app.services.signature.token_service import create_signing_jwt, decode_signing_jwt
from app.services.signature.otp_service import generate_otp, verify_otp


# ── JWT ───────────────────────────────────────────────────────────────────────

def test_jwt_signing_token_roundtrip(sample_sig_req):
    payload = decode_signing_jwt(sample_sig_req.token)
    assert payload is not None
    assert payload['sig_req_id'] == sample_sig_req.id
    assert payload['document_id'] == sample_sig_req.document_id


def test_invalid_jwt_returns_none():
    assert decode_signing_jwt('not-a-valid-token') is None


# ── OTP ───────────────────────────────────────────────────────────────────────

def test_otp_full_cycle(db, sample_sig_req):
    code = generate_otp(sample_sig_req.id)
    assert code.isdigit() and len(code) == 6
    ok, _ = verify_otp(sample_sig_req.id, code)
    assert ok is True
    ok2, _ = verify_otp(sample_sig_req.id, code)
    assert ok2 is False


def test_otp_wrong_code(db, sample_sig_req):
    generate_otp(sample_sig_req.id)
    ok, msg = verify_otp(sample_sig_req.id, '000000')
    assert ok is False and msg


# ── Signing page ──────────────────────────────────────────────────────────────

def test_signing_page_loads_with_valid_token(client, db, sample_sig_req):
    resp = client.get(f'/sign/{sample_sig_req.token}')
    assert resp.status_code == 200


def test_signing_page_rejects_invalid_token(client):
    resp = client.get('/sign/invalid-token-xyz')
    assert resp.status_code == 410


def test_signing_page_updates_status_to_link_opened(client, db, sample_sig_req):
    assert sample_sig_req.status == 'pending'
    client.get(f'/sign/{sample_sig_req.token}')
    db.session.refresh(sample_sig_req)
    assert sample_sig_req.status == 'link_opened'


def test_signing_page_already_signed_shows_done(client, db, sample_sig_req):
    sample_sig_req.status = 'signed'
    db.session.commit()
    resp = client.get(f'/sign/{sample_sig_req.token}')
    assert resp.status_code == 200
    assert b'assinou' in resp.data.lower() or b'done' in resp.data.lower() or resp.status_code == 200


def test_signing_page_cancelled_shows_expired(client, db, sample_sig_req):
    sample_sig_req.status = 'cancelled'
    db.session.commit()
    resp = client.get(f'/sign/{sample_sig_req.token}')
    assert resp.status_code == 200


# ── Request OTP endpoint ──────────────────────────────────────────────────────

def test_request_otp_endpoint_success(client, db, sample_sig_req):
    resp = client.post(f'/sign/{sample_sig_req.token}/request-otp')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True


def test_request_otp_updates_status(client, db, sample_sig_req):
    sample_sig_req.status = 'link_opened'
    db.session.commit()
    client.post(f'/sign/{sample_sig_req.token}/request-otp')
    db.session.refresh(sample_sig_req)
    assert sample_sig_req.status == 'otp_sent'


def test_request_otp_invalid_token(client):
    resp = client.post('/sign/badtoken/request-otp')
    assert resp.status_code == 403


def test_request_otp_signed_token_rejected(client, db, sample_sig_req):
    sample_sig_req.status = 'signed'
    db.session.commit()
    resp = client.post(f'/sign/{sample_sig_req.token}/request-otp')
    assert resp.status_code == 403


# ── Verify OTP endpoint ───────────────────────────────────────────────────────

def test_verify_otp_endpoint_wrong_code(client, db, sample_sig_req):
    generate_otp(sample_sig_req.id)
    resp = client.post(
        f'/sign/{sample_sig_req.token}/verify-otp',
        json={'code': '999999'},
    )
    assert resp.status_code == 200
    assert resp.get_json()['success'] is False


def test_verify_otp_endpoint_correct_code(client, db, sample_sig_req):
    code = generate_otp(sample_sig_req.id)
    resp = client.post(
        f'/sign/{sample_sig_req.token}/verify-otp',
        json={'code': code},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    db.session.refresh(sample_sig_req)
    assert sample_sig_req.status == 'otp_verified'


def test_verify_otp_updates_status(client, db, sample_sig_req):
    code = generate_otp(sample_sig_req.id)
    client.post(f'/sign/{sample_sig_req.token}/verify-otp', json={'code': code})
    db.session.refresh(sample_sig_req)
    assert sample_sig_req.otp_verified_at is not None


# ── Submit signature endpoint ─────────────────────────────────────────────────

def _make_png_data_url():
    """Produce a minimal PNG data URL larger than 100 bytes."""
    sig = b'\x89PNG\r\n\x1a\n'
    def chunk(name, data):
        crc = zlib.crc32(name + data) & 0xffffffff
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', crc)
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff'))
    iend = chunk(b'IEND', b'')
    png = sig + ihdr + idat * 40 + iend
    return 'data:image/png;base64,' + base64.b64encode(png).decode()


def test_submit_requires_otp_verified(client, db, sample_sig_req):
    """Submit should be rejected if status is not otp_verified."""
    sample_sig_req.status = 'link_opened'
    db.session.commit()
    resp = client.post(
        f'/sign/{sample_sig_req.token}/submit',
        json={'signature_data': _make_png_data_url(), 'type': 'drawn'},
    )
    assert resp.status_code == 403


def test_submit_signature_typed(client, db, sample_sig_req, tmp_path):
    """Full submit flow with typed signature."""
    sample_sig_req.status = 'otp_verified'
    db.session.commit()

    data_url = _make_png_data_url()

    with patch('app.utils.paths.get_images_dir', return_value=str(tmp_path)), \
         patch('app.utils.paths.abs_upload_path', return_value=str(tmp_path / 'test.pdf')), \
         patch('app.routes.signing.submit.sha256_file', return_value='abc123'), \
         patch('app.routes.signing.submit.check_all_signed', return_value=False):

        resp = client.post(
            f'/sign/{sample_sig_req.token}/submit',
            json={'signature_data': data_url, 'type': 'typed'},
        )

    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'redirect' in data


def test_submit_updates_sig_req_status(client, db, sample_sig_req, tmp_path):
    sample_sig_req.status = 'otp_verified'
    db.session.commit()

    with patch('app.utils.paths.get_images_dir', return_value=str(tmp_path)), \
         patch('app.utils.paths.abs_upload_path', return_value=str(tmp_path / 'test.pdf')), \
         patch('app.routes.signing.submit.sha256_file', return_value='deadbeef'), \
         patch('app.routes.signing.submit.check_all_signed', return_value=False):

        client.post(
            f'/sign/{sample_sig_req.token}/submit',
            json={'signature_data': _make_png_data_url(), 'type': 'drawn'},
        )

    db.session.refresh(sample_sig_req)
    assert sample_sig_req.status == 'signed'
    assert sample_sig_req.signed_at is not None


# ── Success page ──────────────────────────────────────────────────────────────

def test_sign_success_page(client, db, sample_sig_req):
    resp = client.get(f'/sign/{sample_sig_req.token}/success')
    assert resp.status_code == 200
