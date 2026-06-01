"""Tests for model methods and properties."""
import json
import pytest
from datetime import datetime, timezone, timedelta


class TestUserModel:
    def test_set_and_check_password(self, db, admin_user):
        assert admin_user.check_password('password123') is True
        assert admin_user.check_password('wrong') is False

    def test_password_hash_is_not_plaintext(self, db, admin_user):
        assert admin_user.password_hash != 'password123'
        assert len(admin_user.password_hash) > 20

    def test_repr(self, admin_user):
        assert admin_user.email in repr(admin_user)

    def test_is_active_default(self, admin_user):
        assert admin_user.is_active is True

    def test_is_superadmin(self, admin_user):
        assert admin_user.is_superadmin is True


class TestOtpTokenModel:
    def test_is_expired_false_for_future(self, db, sample_sig_req):
        from app.models.otp_token import OtpToken
        token = OtpToken(
            signature_request_id=sample_sig_req.id,
            code_hash='abc',
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        db.session.add(token)
        db.session.commit()
        assert token.is_expired() is False

    def test_is_expired_true_for_past(self, db, sample_sig_req):
        from app.models.otp_token import OtpToken
        token = OtpToken(
            signature_request_id=sample_sig_req.id,
            code_hash='abc',
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        db.session.add(token)
        db.session.commit()
        assert token.is_expired() is True

    def test_repr(self, db, sample_sig_req):
        from app.models.otp_token import OtpToken
        token = OtpToken(
            signature_request_id=sample_sig_req.id,
            code_hash='abc',
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db.session.add(token)
        db.session.commit()
        r = repr(token)
        assert 'OtpToken' in r


class TestDocumentModel:
    def test_sheet_snapshot_json_property(self, db, sample_doc):
        sample_doc.sheet_snapshot = {'nome': 'João', 'valor': 1000}
        db.session.commit()
        db.session.refresh(sample_doc)
        assert sample_doc.sheet_snapshot['nome'] == 'João'
        assert sample_doc.sheet_snapshot['valor'] == 1000

    def test_rendered_variables_json_property(self, db, sample_doc):
        sample_doc.rendered_variables = {'contratante': 'Empresa X'}
        db.session.commit()
        db.session.refresh(sample_doc)
        assert sample_doc.rendered_variables['contratante'] == 'Empresa X'

    def test_uuid_auto_generated(self, sample_doc):
        assert sample_doc.uuid is not None
        assert len(sample_doc.uuid) == 36

    def test_repr(self, sample_doc):
        r = repr(sample_doc)
        assert 'Document' in r or sample_doc.title in r


class TestSignatureRequestModel:
    def test_uuid_auto_generated(self, sample_sig_req):
        assert sample_sig_req.uuid is not None
        assert len(sample_sig_req.uuid) == 36

    def test_repr(self, sample_sig_req):
        r = repr(sample_sig_req)
        assert 'SignatureRequest' in r or sample_sig_req.signatory_email in r

    def test_default_method(self, sample_sig_req):
        assert sample_sig_req.method == 'email_otp'
