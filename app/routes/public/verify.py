import os
from flask import Blueprint, render_template, send_file, abort
from app.models.document import Document
from app.services.pdf.hasher import sha256_file
from app.utils.paths import abs_upload_path
import app.services.audit_service as audit
from flask import request

bp = Blueprint('public_verify', __name__, url_prefix='/verify')


@bp.route('/<uuid>')
def verify(uuid):
    doc = Document.query.filter_by(uuid=uuid).first()
    if not doc:
        return render_template('public/verify.html', valid=False,
                               message='Documento não encontrado.')
    hash_ok = False
    current_hash = None
    pdf_path = abs_upload_path(doc.pdf_path) if doc.pdf_path else None
    if pdf_path and os.path.exists(pdf_path):
        current_hash = sha256_file(pdf_path)
        hash_ok = (current_hash == doc.sha256_hash)
    sig_requests = doc.signature_requests.all()
    audit.log('VERIFICATION_CHECKED', document_id=doc.id,
              actor_email='público',
              ip=request.remote_addr, user_agent=request.user_agent.string)
    return render_template('public/verify.html', valid=True, doc=doc,
                           hash_ok=hash_ok, current_hash=current_hash,
                           sig_requests=sig_requests)


@bp.route('/qr/<uuid>')
def verify_qr(uuid):
    return verify(uuid)


@bp.route('/<uuid>/download')
def download_certificate(uuid):
    doc = Document.query.filter_by(uuid=uuid).first_or_404()
    pdf_path = abs_upload_path(doc.pdf_path) if doc.pdf_path else None
    if not pdf_path or not os.path.exists(pdf_path):
        abort(404)
    return send_file(pdf_path, mimetype='application/pdf',
                     as_attachment=True, download_name=f'{doc.title}_assinado.pdf')
