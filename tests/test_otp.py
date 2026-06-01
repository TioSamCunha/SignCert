def test_generate_and_verify_otp(app, db, admin_user):
    from app.models.document import Document
    from app.models.signature_request import SignatureRequest
    from app.models.template import DocumentTemplate
    import os

    with app.app_context():
        tpl = DocumentTemplate(
            user_id=admin_user.id, name='Test',
            html_file_path='/tmp/test.html',
        )
        tpl.variables_schema = []
        db.session.add(tpl)
        db.session.flush()

        doc = Document(template_id=tpl.id, title='Test Doc', created_by=admin_user.id)
        doc.sheet_snapshot = {}
        doc.rendered_variables = {}
        db.session.add(doc)
        db.session.flush()

        sig_req = SignatureRequest(
            document_id=doc.id, signatory_name='Test Signer',
            signatory_email='signer@test.com', created_by=admin_user.id,
        )
        db.session.add(sig_req)
        db.session.commit()

        from app.services.signature.otp_service import generate_otp, verify_otp
        code = generate_otp(sig_req.id)
        assert len(code) == 6
        assert code.isdigit()

        ok, reason = verify_otp(sig_req.id, '000000')
        assert not ok

        ok, reason = verify_otp(sig_req.id, code)
        assert ok

        ok2, reason2 = verify_otp(sig_req.id, code)
        assert not ok2


def test_jwt_token(app):
    with app.app_context():
        from app.services.signature.token_service import create_signing_jwt, decode_signing_jwt
        token = create_signing_jwt(5, 3, 'email@test.com', 1)
        payload = decode_signing_jwt(token)
        assert payload['sig_req_id'] == 5
        assert payload['document_id'] == 3
        assert payload['email'] == 'email@test.com'
