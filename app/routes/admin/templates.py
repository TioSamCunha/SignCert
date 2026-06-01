import io
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.models.template import DocumentTemplate
from app.models.sheet_connection import SheetConnection
from app.services.pdf.renderer import (extract_variables, render_to_html,
                                        html_to_pdf, save_template_file, load_template_html)

bp = Blueprint('admin_templates', __name__, url_prefix='/admin/templates')


@bp.route('/')
@login_required
def list_templates():
    templates = DocumentTemplate.query.filter_by(is_active=True).all()
    return render_template('admin/templates/list.html', templates=templates)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_template():
    sheets = SheetConnection.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        html_content = request.form.get('html_content', '').strip()
        tpl = DocumentTemplate(
            user_id=current_user.id,
            name=request.form['name'].strip(),
            description=request.form.get('description', '').strip(),
            html_file_path='',
            sheet_connection_id=request.form.get('sheet_connection_id') or None,
        )
        tpl.variables_schema = [{'name': v, 'label': v} for v in extract_variables(html_content)]
        db.session.add(tpl)
        db.session.flush()
        tpl.html_file_path = save_template_file(tpl.id, html_content)
        db.session.commit()
        flash('Template criado com sucesso.', 'success')
        return redirect(url_for('admin_templates.list_templates'))
    return render_template('admin/templates/form.html', action='new', sheets=sheets)


@bp.route('/<int:tpl_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template(tpl_id):
    tpl = DocumentTemplate.query.get_or_404(tpl_id)
    sheets = SheetConnection.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        html_content = request.form.get('html_content', '').strip()
        tpl.name = request.form['name'].strip()
        tpl.description = request.form.get('description', '').strip()
        tpl.sheet_connection_id = request.form.get('sheet_connection_id') or None
        tpl.variables_schema = [{'name': v, 'label': v} for v in extract_variables(html_content)]
        tpl.html_file_path = save_template_file(tpl.id, html_content)
        db.session.commit()
        flash('Template atualizado.', 'success')
        return redirect(url_for('admin_templates.list_templates'))
    html_content = load_template_html(tpl.html_file_path) if tpl.html_file_path else ''
    return render_template('admin/templates/form.html', tpl=tpl, action='edit',
                           sheets=sheets, html_content=html_content)


@bp.route('/<int:tpl_id>/delete', methods=['POST'])
@login_required
def delete_template(tpl_id):
    tpl = DocumentTemplate.query.get_or_404(tpl_id)
    tpl.is_active = False
    db.session.commit()
    flash('Template removido.', 'info')
    return redirect(url_for('admin_templates.list_templates'))


@bp.route('/<int:tpl_id>/preview-pdf', methods=['POST'])
@login_required
def preview_pdf(tpl_id):
    tpl = DocumentTemplate.query.get_or_404(tpl_id)
    html_content = load_template_html(tpl.html_file_path)
    sample = {v['name']: f'[{v["name"]}]' for v in tpl.variables_schema}
    rendered = render_to_html(html_content, sample)
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = tmp.name
    html_to_pdf(rendered, tmp_path)
    with open(tmp_path, 'rb') as f:
        pdf_bytes = f.read()
    os.unlink(tmp_path)
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name=f'preview_{tpl.name}.pdf')
