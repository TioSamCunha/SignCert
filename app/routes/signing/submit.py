from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from app.extensions import db
from app.models.signature_request import SignatureRequest
from app.models.document import Document
from app.services.signature.token_service import decode_signing_jwt
from app.services.signature.record_service import record_signature
from app.services.signature.finalize_service import check_all_signed, finalize_document
from app.services.pdf.hasher import sha256_file
import app.services.audit_service as audit
from app.services.email.notifications import send_signed_notification

bp = Blueprint('signing_submit', __name__, url_prefix='/sign')


def _load_sig_req(token: str):
    payload = decode_signing_jwt(token)
    if not payload:
        return None
    sig_req = SignatureRequest.query.get(payload.get('sig_req_id'))
    if not sig_req or sig_req.token != token:
        return None
    return sig_req


@bp.route('/<token>/submit', methods=['POST'])
def submit(token):
    sig_req = _load_sig_req(token)
    if not sig_req or sig_req.status != 'otp_verified':
        return jsonify({'success': False,
                        'message': 'Verificação OTP necessária antes de assinar.'}), 403
    data = request.json or {}
    data_url = data.get('signature_data', '')
    sig_type = data.get('type', 'drawn')
    doc = Document.query.get(sig_req.document_id)
    doc_hash = sha256_file(doc.draft_pdf_path) if doc.draft_pdf_path else ''
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    ua = request.user_agent.string
    try:
        record_signature(sig_req, data_url, sig_type, ip, ua, doc_hash)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    audit.log('SIGNATURE_SUBMITTED', document_id=doc.id,
              signature_request_id=sig_req.id,
              actor_email=sig_req.signatory_email,
              details={'type': sig_type, 'hash': doc_hash},
              ip=ip, user_agent=ua)
    try:
        from flask import current_app
        send_signed_notification(doc, sig_req, current_app.config.get('FIRM_EMAIL', ''))
    except Exception:
        pass
    if check_all_signed(doc.id):
        try:
            finalize_document(doc.id)
        except Exception:
            pass
    elif doc.status == 'pending_signatures':
        doc.status = 'partially_signed'
        db.session.commit()
    return jsonify({'success': True, 'redirect': url_for('signing_view.sign_success', token=token)})


@bp.route('/<token>/success')
def sign_success(token):
    payload = decode_signing_jwt(token) or {}
    sig_req = SignatureRequest.query.get(payload.get('sig_req_id'))
    return render_template('signing/success.html', sig_req=sig_req)
