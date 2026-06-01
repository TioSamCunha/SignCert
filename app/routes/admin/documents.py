import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.models.document import Document
from app.models.template import DocumentTemplate
from app.models.sheet_connection import SheetConnection
from app.services.pdf.renderer import load_template_html, render_to_html, html_to_pdf
from app.services.pdf.hasher import sha256_file
from app.services.sheets.reader import get_row_by_index, get_all_rows
from app.utils.paths import get_pdf_dir, abs_upload_path
import app.services.audit_service as audit

bp = Blueprint('admin_documents', __name__, url_prefix='/admin/documents')


@bp.route('/')
@login_required
def list_documents():
    docs = Document.query.order_by(Document.created_at.desc()).all()
    return render_template('admin/documents/list.html', docs=docs)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_document():
    templates = DocumentTemplate.query.filter_by(is_active=True).all()
    sheets = SheetConnection.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        tpl = DocumentTemplate.query.get_or_404(request.form['template_id'])
        html_content = load_template_html(tpl.html_file_path)
        variables = {}
        sheet_id = request.form.get('sheet_connection_id')
        row_index = request.form.get('row_index')
        sheet_snapshot = {}
        if sheet_id and row_index:
            conn = SheetConnection.query.get(sheet_id)
            sheet_snapshot = get_row_by_index(conn, int(row_index))
            variables = dict(sheet_snapshot)
        for var in tpl.variables_schema:
            manual = request.form.get(f'var_{var["name"]}')
            if manual:
                variables[var['name']] = manual
        rendered_html = render_to_html(html_content, variables)
        doc = Document(
            template_id=tpl.id,
            sheet_connection_id=int(sheet_id) if sheet_id else None,
            sheet_row_index=int(row_index) if row_index else None,
            title=request.form['title'].strip(),
            created_by=current_user.id,
        )
        doc.sheet_snapshot = sheet_snapshot
        doc.rendered_variables = variables
        db.session.add(doc)
        db.session.flush()
        pdf_dir = get_pdf_dir()
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, f'doc_{doc.id}_draft.pdf')
        html_to_pdf(rendered_html, pdf_path)
        doc.draft_pdf_path = pdf_path
        doc.sha256_draft_hash = sha256_file(pdf_path)
        db.session.commit()
        audit.log('DOCUMENT_CREATED', document_id=doc.id,
                  user_id=current_user.id, actor_email=current_user.email,
                  ip=request.remote_addr)
        flash('Documento gerado com sucesso.', 'success')
        return redirect(url_for('admin_documents.document_detail', doc_id=doc.id))
    return render_template('admin/documents/new.html', templates=templates, sheets=sheets)


@bp.route('/<int:doc_id>/')
@login_required
def document_detail(doc_id):
    doc = Document.query.get_or_404(doc_id)
    sig_requests = doc.signature_requests.all()
    trail = audit.get_document_trail(doc_id)
    return render_template('admin/documents/detail.html',
                           doc=doc, sig_requests=sig_requests, trail=trail)


@bp.route('/<int:doc_id>/download')
@login_required
def download_pdf(doc_id):
    doc = Document.query.get_or_404(doc_id)
    pdf_path = abs_upload_path(doc.pdf_path or doc.draft_pdf_path or '')
    if not pdf_path or not os.path.exists(pdf_path):
        flash('PDF não disponível.', 'warning')
        return redirect(url_for('admin_documents.document_detail', doc_id=doc_id))
    return send_file(pdf_path, mimetype='application/pdf',
                     as_attachment=True, download_name=f'{doc.title}.pdf')


@bp.route('/<int:doc_id>/cancel', methods=['POST'])
@login_required
def cancel_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    doc.status = 'cancelled'
    for sr in doc.signature_requests.filter_by(status='pending').all():
        sr.status = 'cancelled'
    db.session.commit()
    audit.log('DOCUMENT_CANCELLED', document_id=doc_id,
              user_id=current_user.id, actor_email=current_user.email)
    flash('Documento cancelado.', 'warning')
    return redirect(url_for('admin_documents.document_detail', doc_id=doc_id))
