from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.document import Document
from app.models.signature_request import SignatureRequest
from app.services.signature.token_service import create_signing_jwt
from app.services.email.invites import send_signing_invitation
import app.services.audit_service as audit

bp = Blueprint('admin_signatories', __name__, url_prefix='/admin/signatures')


@bp.route('/')
@login_required
def list_requests():
    reqs = SignatureRequest.query.order_by(SignatureRequest.created_at.desc()).all()
    return render_template('admin/signatures/list.html', reqs=reqs)


@bp.route('/send/<int:doc_id>', methods=['GET', 'POST'])
@login_required
def send_request(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if request.method == 'POST':
        name = request.form['signatory_name'].strip()
        email = request.form['signatory_email'].strip().lower()
        cpf = request.form.get('signatory_cpf', '').strip() or None
        phone = request.form.get('signatory_phone', '').strip() or None
        method = request.form.get('method', 'email_otp')
        order = int(request.form.get('signing_order', 1))
        sig_req = SignatureRequest(
            document_id=doc.id, signatory_name=name,
            signatory_email=email, signatory_cpf=cpf,
            signatory_phone=phone, method=method,
            signing_order=order, created_by=current_user.id,
        )
        db.session.add(sig_req)
        db.session.flush()
        token = create_signing_jwt(sig_req.id, doc.id, email)
        hours = current_app.config.get('SIGNING_TOKEN_EXPIRES_HOURS', 72)
        sig_req.token = token
        sig_req.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        db.session.commit()
        signing_url = url_for('signing_view.sign', token=token, _external=True)
        try:
            send_signing_invitation(sig_req, signing_url)
            sig_req.email_sent_at = datetime.now(timezone.utc)
            db.session.commit()
        except Exception as e:
            flash(f'Aviso: e-mail não enviado ({e}). Link: {signing_url}', 'warning')
        if doc.status == 'draft':
            doc.status = 'pending_signatures'
            db.session.commit()
        audit.log('DOCUMENT_SENT', document_id=doc.id,
                  user_id=current_user.id, actor_email=current_user.email,
                  details={'signatory': email, 'method': method})
        flash(f'Convite enviado para {email}.', 'success')
        return redirect(url_for('admin_documents.document_detail', doc_id=doc.id))
    return render_template('admin/signatures/send.html', doc=doc)


@bp.route('/<int:req_id>/resend', methods=['POST'])
@login_required
def resend_request(req_id):
    sig_req = SignatureRequest.query.get_or_404(req_id)
    token = create_signing_jwt(sig_req.id, sig_req.document_id, sig_req.signatory_email)
    hours = current_app.config.get('SIGNING_TOKEN_EXPIRES_HOURS', 72)
    sig_req.token = token
    sig_req.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
    sig_req.status = 'pending'
    db.session.commit()
    signing_url = url_for('signing_view.sign', token=token, _external=True)
    try:
        send_signing_invitation(sig_req, signing_url)
        sig_req.email_sent_at = datetime.now(timezone.utc)
        db.session.commit()
    except Exception as e:
        flash(f'Erro ao enviar e-mail: {e}', 'danger')
        return redirect(url_for('admin_documents.document_detail',
                                doc_id=sig_req.document_id))
    audit.log('REQUEST_RESENT', document_id=sig_req.document_id,
              signature_request_id=sig_req.id,
              user_id=current_user.id, actor_email=current_user.email)
    flash('Convite reenviado.', 'success')
    return redirect(url_for('admin_documents.document_detail', doc_id=sig_req.document_id))


@bp.route('/<int:req_id>/cancel', methods=['POST'])
@login_required
def cancel_request(req_id):
    sig_req = SignatureRequest.query.get_or_404(req_id)
    sig_req.status = 'cancelled'
    db.session.commit()
    audit.log('REQUEST_CANCELLED', document_id=sig_req.document_id,
              signature_request_id=sig_req.id,
              user_id=current_user.id, actor_email=current_user.email)
    flash('Pedido cancelado.', 'info')
    return redirect(url_for('admin_documents.document_detail', doc_id=sig_req.document_id))
