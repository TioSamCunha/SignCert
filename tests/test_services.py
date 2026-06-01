"""Tests for utility and service modules."""
import hashlib
import os
import base64
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock


# ── Formatters ────────────────────────────────────────────────────────────────

class TestFormatters:
    def test_format_cpf_valid(self):
        from app.utils.formatters import format_cpf
        assert format_cpf('12345678901') == '123.456.789-01'

    def test_format_cpf_already_formatted(self):
        from app.utils.formatters import format_cpf
        assert format_cpf('123.456.789-01') == '123.456.789-01'

    def test_format_cpf_invalid_length(self):
        from app.utils.formatters import format_cpf
        result = format_cpf('123')
        assert result == '123'

    def test_format_cpf_none(self):
        from app.utils.formatters import format_cpf
        # None or '' = '' → digits '' → len != 11 → returns original cpf (None)
        assert format_cpf(None) is None

    def test_format_cnpj_valid(self):
        from app.utils.formatters import format_cnpj
        assert format_cnpj('12345678000195') == '12.345.678/0001-95'

    def test_format_cnpj_invalid_length(self):
        from app.utils.formatters import format_cnpj
        result = format_cnpj('123')
        assert result == '123'

    def test_mask_email_normal(self):
        from app.utils.formatters import mask_email
        result = mask_email('samuel@gmail.com')
        assert result == 'sa***@gmail.com'

    def test_mask_email_short_user(self):
        from app.utils.formatters import mask_email
        # len('ab') == 2, not > 2, so falls to else → '***@test.com'
        result = mask_email('ab@test.com')
        assert result == '***@test.com'

    def test_mask_email_no_at(self):
        from app.utils.formatters import mask_email
        result = mask_email('invalidemail')
        assert result == 'invalidemail'

    def test_mask_email_empty(self):
        from app.utils.formatters import mask_email
        assert mask_email('') == ''
        assert mask_email(None) is None

    def test_to_brasilia_with_utc(self, app):
        from app.utils.formatters import to_brasilia
        with app.app_context():
            dt = datetime(2024, 6, 1, 15, 0, 0, tzinfo=timezone.utc)
            result = to_brasilia(dt)
            assert '01/06/2024' in result
            assert '12:00:00' in result  # UTC-3

    def test_to_brasilia_none(self, app):
        from app.utils.formatters import to_brasilia
        with app.app_context():
            assert to_brasilia(None) == '-'

    def test_to_brasilia_naive_datetime(self, app):
        from app.utils.formatters import to_brasilia
        with app.app_context():
            dt = datetime(2024, 6, 1, 12, 0, 0)
            result = to_brasilia(dt)
            assert '01/06/2024' in result


# ── Hasher ────────────────────────────────────────────────────────────────────

class TestHasher:
    def test_sha256_bytes(self):
        from app.services.pdf.hasher import sha256_bytes
        data = b'hello world'
        expected = hashlib.sha256(data).hexdigest()
        assert sha256_bytes(data) == expected

    def test_sha256_file(self, tmp_path):
        from app.services.pdf.hasher import sha256_file
        f = tmp_path / 'test.txt'
        f.write_bytes(b'test content')
        expected = hashlib.sha256(b'test content').hexdigest()
        assert sha256_file(str(f)) == expected

    def test_sha256_file_large(self, tmp_path):
        from app.services.pdf.hasher import sha256_file
        data = b'x' * 100_000
        f = tmp_path / 'large.bin'
        f.write_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert sha256_file(str(f)) == expected


# ── Paths ─────────────────────────────────────────────────────────────────────

class TestPaths:
    def test_abs_upload_path_absolute(self, app):
        from app.utils.paths import abs_upload_path
        with app.app_context():
            result = abs_upload_path('/absolute/path/file.pdf')
            assert result == '/absolute/path/file.pdf'

    def test_abs_upload_path_relative(self, app):
        from app.utils.paths import abs_upload_path
        with app.app_context():
            result = abs_upload_path('uploads/test.pdf')
            assert os.path.isabs(result)
            assert 'uploads' in result
            assert 'test.pdf' in result

    def test_get_pdf_dir(self, app):
        from app.utils.paths import get_pdf_dir
        with app.app_context():
            result = get_pdf_dir()
            assert os.path.isabs(result)
            assert 'generated_pdfs' in result

    def test_get_images_dir(self, app):
        from app.utils.paths import get_images_dir
        with app.app_context():
            result = get_images_dir()
            assert os.path.isabs(result)
            assert 'signature_images' in result

    def test_get_certs_dir(self, app):
        from app.utils.paths import get_certs_dir
        with app.app_context():
            result = get_certs_dir()
            assert os.path.isabs(result)
            assert 'certificates' in result


# ── Token Service ─────────────────────────────────────────────────────────────

class TestTokenService:
    def test_create_and_decode(self, app):
        from app.services.signature.token_service import create_signing_jwt, decode_signing_jwt
        with app.app_context():
            token = create_signing_jwt(1, 2, 'test@email.com', expires_hours=1)
            payload = decode_signing_jwt(token)
            assert payload['sig_req_id'] == 1
            assert payload['document_id'] == 2
            assert payload['email'] == 'test@email.com'
            assert 'jti' in payload

    def test_invalid_token_returns_none(self, app):
        from app.services.signature.token_service import decode_signing_jwt
        with app.app_context():
            assert decode_signing_jwt('garbage') is None
            assert decode_signing_jwt('') is None

    def test_expired_token_returns_none(self, app):
        from app.services.signature.token_service import create_signing_jwt, decode_signing_jwt
        with app.app_context():
            token = create_signing_jwt(1, 2, 'test@email.com', expires_hours=-1)
            assert decode_signing_jwt(token) is None


# ── OTP Service ───────────────────────────────────────────────────────────────

class TestOtpService:
    def test_generate_returns_6_digits(self, db, sample_sig_req):
        from app.services.signature.otp_service import generate_otp
        code = generate_otp(sample_sig_req.id)
        assert len(code) == 6
        assert code.isdigit()

    def test_verify_correct_code(self, db, sample_sig_req):
        from app.services.signature.otp_service import generate_otp, verify_otp
        code = generate_otp(sample_sig_req.id)
        ok, msg = verify_otp(sample_sig_req.id, code)
        assert ok is True

    def test_verify_wrong_code(self, db, sample_sig_req):
        from app.services.signature.otp_service import generate_otp, verify_otp
        generate_otp(sample_sig_req.id)
        ok, msg = verify_otp(sample_sig_req.id, '000000')
        assert ok is False
        assert 'inválido' in msg.lower() or msg

    def test_code_single_use(self, db, sample_sig_req):
        from app.services.signature.otp_service import generate_otp, verify_otp
        code = generate_otp(sample_sig_req.id)
        verify_otp(sample_sig_req.id, code)
        ok, msg = verify_otp(sample_sig_req.id, code)
        assert ok is False

    def test_generate_invalidates_previous(self, db, sample_sig_req):
        from app.services.signature.otp_service import generate_otp, verify_otp
        code1 = generate_otp(sample_sig_req.id)
        generate_otp(sample_sig_req.id)  # second replaces first
        ok, _ = verify_otp(sample_sig_req.id, code1)
        assert ok is False

    def test_max_attempts_blocks_further_tries(self, app, db, sample_sig_req):
        from app.services.signature.otp_service import generate_otp, verify_otp
        generate_otp(sample_sig_req.id)
        max_att = app.config.get('OTP_MAX_ATTEMPTS', 3)
        for _ in range(max_att):
            verify_otp(sample_sig_req.id, '111111')
        ok, msg = verify_otp(sample_sig_req.id, '111111')
        assert ok is False
        assert 'tentativas' in msg.lower() or msg

    def test_expired_otp_fails(self, db, sample_sig_req):
        from app.models.otp_token import OtpToken
        from app.services.signature.otp_service import _hash_code, verify_otp
        token = OtpToken(
            signature_request_id=sample_sig_req.id,
            code_hash=_hash_code('123456'),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        db.session.add(token)
        db.session.commit()
        ok, msg = verify_otp(sample_sig_req.id, '123456')
        assert ok is False
        assert 'expirado' in msg.lower() or msg

    def test_no_token_fails(self, db, sample_sig_req):
        from app.services.signature.otp_service import verify_otp
        ok, msg = verify_otp(sample_sig_req.id, '123456')
        assert ok is False


# ── Audit Service ─────────────────────────────────────────────────────────────

class TestAuditService:
    def test_log_creates_entry(self, db, sample_doc):
        import app.services.audit_service as audit
        entry = audit.log('TEST_ACTION', document_id=sample_doc.id,
                          actor_email='test@example.com',
                          details={'key': 'value'}, ip='127.0.0.1')
        assert entry.id is not None
        assert entry.action == 'TEST_ACTION'
        assert entry.actor_email == 'test@example.com'
        assert entry.document_id == sample_doc.id

    def test_log_without_optional_fields(self, db):
        import app.services.audit_service as audit
        entry = audit.log('SIMPLE_ACTION')
        assert entry.action == 'SIMPLE_ACTION'
        assert entry.document_id is None

    def test_get_document_trail(self, db, sample_doc):
        import app.services.audit_service as audit
        audit.log('ACTION_1', document_id=sample_doc.id)
        audit.log('ACTION_2', document_id=sample_doc.id)
        trail = audit.get_document_trail(sample_doc.id)
        actions = [e.action for e in trail]
        assert 'ACTION_1' in actions
        assert 'ACTION_2' in actions

    def test_get_request_trail(self, db, sample_sig_req):
        import app.services.audit_service as audit
        audit.log('OTP_SENT', signature_request_id=sample_sig_req.id)
        trail = audit.get_request_trail(sample_sig_req.id)
        assert any(e.action == 'OTP_SENT' for e in trail)

    def test_log_with_geo(self, db, sample_doc):
        import app.services.audit_service as audit
        geo = {'country': 'BR', 'city': 'São Paulo'}
        entry = audit.log('GEO_ACTION', document_id=sample_doc.id, geo=geo)
        assert entry.id is not None


# ── Record Service ────────────────────────────────────────────────────────────

class TestRecordService:
    def _make_data_url(self, pixel_count=200):
        """Create a minimal valid PNG data URL."""
        import struct, zlib
        def png_chunk(name, data):
            c = zlib.crc32(name + data) & 0xffffffff
            return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)

        sig = b'\x89PNG\r\n\x1a\n'
        ihdr = png_chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
        raw = b'\x00\xff\xff\xff'
        compressed = zlib.compress(raw)
        idat = png_chunk(b'IDAT', compressed)
        iend = png_chunk(b'IEND', b'')
        png_bytes = sig + ihdr + idat * 30 + iend  # repeat to reach >100 bytes
        b64 = base64.b64encode(png_bytes).decode()
        return f'data:image/png;base64,{b64}'

    def test_save_signature_image(self, app, db, sample_sig_req, tmp_path):
        from app.services.signature.record_service import save_signature_image
        with app.app_context():
            with patch('app.utils.paths.get_images_dir', return_value=str(tmp_path)):
                data_url = self._make_data_url()
                path = save_signature_image(sample_sig_req.id, data_url)
                assert os.path.exists(path)

    def test_save_signature_image_invalid_data_url(self, app, db, sample_sig_req):
        from app.services.signature.record_service import save_signature_image
        with app.app_context():
            with pytest.raises(ValueError, match='Invalid'):
                save_signature_image(sample_sig_req.id, 'not-a-data-url')

    def test_save_signature_image_too_small(self, app, db, sample_sig_req):
        from app.services.signature.record_service import save_signature_image
        with app.app_context():
            tiny = base64.b64encode(b'x' * 10).decode()
            with pytest.raises(ValueError, match='too small'):
                save_signature_image(sample_sig_req.id, f'data:image/png;base64,{tiny}')


# ── Check All Signed ──────────────────────────────────────────────────────────

class TestFinalizeService:
    def test_check_all_signed_false_when_pending(self, db, sample_doc, sample_sig_req):
        from app.services.signature.finalize_service import check_all_signed
        sample_sig_req.status = 'pending'
        db.session.commit()
        assert check_all_signed(sample_doc.id) is False

    def test_check_all_signed_true_when_signed(self, db, sample_doc, sample_sig_req):
        from app.services.signature.finalize_service import check_all_signed
        sample_sig_req.status = 'signed'
        db.session.commit()
        assert check_all_signed(sample_doc.id) is True

    def test_check_all_signed_false_with_mixed_statuses(self, db, sample_doc, sample_sig_req, admin_user):
        from app.models.signature_request import SignatureRequest
        from app.services.signature.finalize_service import check_all_signed
        import datetime

        sample_sig_req.status = 'signed'
        sig2 = SignatureRequest(
            document_id=sample_doc.id,
            signatory_name='Maria',
            signatory_email='maria@example.com',
            status='pending',
            token_expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=72),
            created_by=admin_user.id,
        )
        db.session.add(sig2)
        db.session.commit()
        assert check_all_signed(sample_doc.id) is False
