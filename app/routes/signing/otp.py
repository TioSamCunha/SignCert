from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.signature_request import SignatureRequest
from app.services.signature.token_service import decode_signing_jwt
from app.services.signature.otp_service import generate_otp, verify_otp
from app.services.email.otp_emails import send_otp_code
from app.utils.formatters import mask_email
import app.services.audit_service as audit

bp = Blueprint('signing_otp', __name__, url_prefix='/sign')


def _load_sig_req(token: str):
    payload = decode_signing_jwt(token)
    if not payload:
        return None
    sig_req = SignatureRequest.query.get(payload.get('sig_req_id'))
    if not sig_req or sig_req.token != token:
        return None
    if sig_req.status in ('signed', 'cancelled', 'expired'):
        return None
    return sig_req


@bp.route('/<token>/request-otp', methods=['POST'])
def request_otp(token):
    sig_req = _load_sig_req(token)
    if not sig_req:
        return jsonify({'success': False, 'message': 'Link inválido ou expirado.'}), 403
    code = generate_otp(sig_req.id)
    try:
        send_otp_code(sig_req, code)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao enviar e-mail: {e}'}), 500
    sig_req.otp_sent_at = datetime.now(timezone.utc)
    if sig_req.status in ('link_opened', 'pending'):
        sig_req.status = 'otp_sent'
    db.session.commit()
    audit.log('OTP_SENT', document_id=sig_req.document_id,
              signature_request_id=sig_req.id,
              actor_email=sig_req.signatory_email,
              ip=request.remote_addr)
    return jsonify({'success': True,
                    'message': f'Código enviado para {mask_email(sig_req.signatory_email)}'})


@bp.route('/<token>/verify-otp', methods=['POST'])
def verify_otp_route(token):
    sig_req = _load_sig_req(token)
    if not sig_req:
        return jsonify({'success': False, 'message': 'Link inválido ou expirado.'}), 403
    code = (request.json or {}).get('code', '').strip()
    ok, reason = verify_otp(sig_req.id, code)
    if ok:
        sig_req.otp_verified_at = datetime.now(timezone.utc)
        sig_req.status = 'otp_verified'
        db.session.commit()
        audit.log('OTP_VERIFIED', document_id=sig_req.document_id,
                  signature_request_id=sig_req.id,
                  actor_email=sig_req.signatory_email,
                  ip=request.remote_addr)
        return jsonify({'success': True})
    audit.log('OTP_FAILED', document_id=sig_req.document_id,
              signature_request_id=sig_req.id,
              actor_email=sig_req.signatory_email,
              details={'reason': reason}, ip=request.remote_addr)
    return jsonify({'success': False, 'message': reason})
