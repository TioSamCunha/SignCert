"""
Route for ICP-Brasil digital certificate signing.
Supports two modes:
  1. Browser-side: browser sends pre-computed pkcs7_signature + cert_chain_pem
  2. Server-side (default): browser uploads .pfx, server parses and signs in memory
"""
import base64
import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template, url_for
from app.extensions import db
from app.models.signature_request import SignatureRequest
from app.models.document import Document
from app.services.signature.token_service import decode_signing_jwt
from app.services.digital_cert.validator import validate_icp_brasil_chain, extract_signer_info
from app.services.digital_cert.signer import embed_digital_signature
from app.services.pdf.hasher import sha256_file
from app.services.signature.finalize_service import check_all_signed, finalize_document
import app.services.audit_service as audit

bp = Blueprint('signing_digital_cert', __name__, url_prefix='/sign')


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


@bp.route('/<token>/digital-cert', methods=['GET'])
def digital_cert_page(token):
    sig_req = _load_sig_req(token)
    if not sig_req:
        return render_template('signing/expired.html'), 410
    doc = Document.query.get(decode_signing_jwt(token)['document_id'])
    return render_template('signing/digital_cert.html',
                           sig_req=sig_req, doc=doc, token=token)


@bp.route('/<token>/submit-cert', methods=['POST'])
def submit_cert(token):
    sig_req = _load_sig_req(token)
    if not sig_req:
        return jsonify({'success': False, 'message': 'Link inválido ou expirado.'}), 403

    data = request.json or {}
    pkcs7_b64 = data.get('pkcs7_signature', '')
    cert_chain_pem = data.get('cert_chain_pem', [])
    if not pkcs7_b64 or not cert_chain_pem:
        return jsonify({'success': False, 'message': 'Dados de assinatura incompletos.'}), 400

    valid, msg = validate_icp_brasil_chain(cert_chain_pem)
    if not valid:
        return jsonify({'success': False, 'message': msg}), 400

    signer_info = extract_signer_info(cert_chain_pem[0])
    doc = Document.query.get(sig_req.document_id)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

    from flask import current_app
    pdf_dir = current_app.config.get('GENERATED_PDFS_DIR', 'uploads/generated_pdfs')
    signed_path = os.path.join(pdf_dir, f'doc_{doc.id}_cert_{sig_req.id}.pdf')

    try:
        embed_digital_signature(
            doc.draft_pdf_path, pkcs7_b64, cert_chain_pem,
            sig_req.signatory_name, signed_path)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao embedar assinatura: {e}'}), 500

    doc_hash = sha256_file(doc.draft_pdf_path)
    sig_req.signature_type = 'digital_cert'
    sig_req.document_hash_at_signing = doc_hash
    sig_req.signed_at = datetime.now(timezone.utc)
    sig_req.status = 'signed'
    sig_req.ip_address = ip
    db.session.commit()

    audit.log('SIGNATURE_SUBMITTED', document_id=doc.id,
              signature_request_id=sig_req.id,
              actor_email=sig_req.signatory_email,
              details={'type': 'digital_cert_icp_brasil',
                       'cert_subject': signer_info.get('name'),
                       'hash': doc_hash},
              ip=ip, user_agent=request.user_agent.string)

    if check_all_signed(doc.id):
        try:
            finalize_document(doc.id)
        except Exception:
            pass
    elif doc.status == 'pending_signatures':
        doc.status = 'partially_signed'
        db.session.commit()

    return jsonify({'success': True,
                    'redirect': url_for('signing_submit.sign_success', token=token)})


@bp.route('/<token>/submit-pfx', methods=['POST'])
def submit_pfx(token):
    """Server-side .pfx parsing: browser sends base64(pfx) + password over HTTPS."""
    sig_req = _load_sig_req(token)
    if not sig_req:
        return jsonify({'success': False, 'message': 'Link inválido ou expirado.'}), 403

    data = request.json or {}
    pfx_b64 = data.get('pfx_b64', '')
    password = data.get('password', '')
    if not pfx_b64:
        return jsonify({'success': False, 'message': 'Arquivo .pfx não recebido.'}), 400

    try:
        from app.services.digital_cert.pfx_signer import sign_pdf_hash
        pfx_bytes = base64.b64decode(pfx_b64)
        doc = Document.query.get(sig_req.document_id)

        with open(doc.draft_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        result = sign_pdf_hash(pdf_bytes, pfx_bytes, password)
    except ValueError as e:
        return jsonify({'success': False, 'message': f'Erro ao processar certificado: {e}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Certificado inválido ou senha incorreta: {e}'}), 400

    cert_chain = [result['cert_pem']] + result['chain_pems']
    valid, msg = validate_icp_brasil_chain(cert_chain)
    if not valid:
        return jsonify({'success': False, 'message': msg}), 400

    signer_info = extract_signer_info(cert_chain[0])
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

    from flask import current_app
    pdf_dir = current_app.config.get('GENERATED_PDFS_DIR', 'uploads/generated_pdfs')
    signed_path = os.path.join(pdf_dir, f'doc_{doc.id}_cert_{sig_req.id}.pdf')

    try:
        embed_digital_signature(doc.draft_pdf_path, result['signature_b64'],
                                cert_chain, sig_req.signatory_name, signed_path)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao incorporar assinatura: {e}'}), 500

    sig_req.signature_type = 'digital_cert'
    sig_req.document_hash_at_signing = result['pdf_hash_hex']
    sig_req.signed_at = datetime.now(timezone.utc)
    sig_req.status = 'signed'
    sig_req.ip_address = ip
    db.session.commit()

    audit.log('SIGNATURE_SUBMITTED', document_id=doc.id,
              signature_request_id=sig_req.id,
              actor_email=sig_req.signatory_email,
              details={'type': 'digital_cert_server_side',
                       'cert_subject': signer_info.get('name'),
                       'hash': result['pdf_hash_hex']},
              ip=ip, user_agent=request.user_agent.string)

    if check_all_signed(doc.id):
        try:
            finalize_document(doc.id)
        except Exception:
            pass
    elif doc.status == 'pending_signatures':
        doc.status = 'partially_signed'
        db.session.commit()

    return jsonify({'success': True,
                    'redirect': url_for('signing_submit.sign_success', token=token)})
