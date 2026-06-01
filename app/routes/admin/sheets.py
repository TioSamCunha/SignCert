from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.sheet_connection import SheetConnection
from app.services.sheets.connector import encrypt_credentials
from app.services.sheets.validator import validate_connection
from app.services.sheets.reader import get_headers, get_rows_preview, get_all_rows

bp = Blueprint('admin_sheets', __name__, url_prefix='/admin/sheets')


@bp.route('/')
@login_required
def list_sheets():
    sheets = SheetConnection.query.filter_by(is_active=True).all()
    return render_template('admin/sheets/list.html', sheets=sheets)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_sheet():
    if request.method == 'POST':
        creds_json = request.form.get('service_account_json', '').strip()
        spreadsheet_id = request.form.get('spreadsheet_id', '').strip()
        tab_name = request.form.get('sheet_tab_name', 'Sheet1').strip()
        ok, msg = validate_connection(spreadsheet_id, tab_name, creds_json)
        if not ok:
            flash(msg, 'danger')
            return render_template('admin/sheets/form.html', action='new')
        conn = SheetConnection(
            user_id=current_user.id,
            display_name=request.form['display_name'].strip(),
            spreadsheet_id=spreadsheet_id,
            sheet_tab_name=tab_name,
            service_account_json=encrypt_credentials(creds_json),
            header_row=int(request.form.get('header_row', 1)),
        )
        db.session.add(conn)
        db.session.commit()
        flash('Planilha conectada com sucesso.', 'success')
        return redirect(url_for('admin_sheets.list_sheets'))
    return render_template('admin/sheets/form.html', action='new')


@bp.route('/<int:sheet_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_sheet(sheet_id):
    conn = SheetConnection.query.get_or_404(sheet_id)
    if request.method == 'POST':
        conn.display_name = request.form['display_name'].strip()
        conn.sheet_tab_name = request.form.get('sheet_tab_name', 'Sheet1').strip()
        conn.header_row = int(request.form.get('header_row', 1))
        db.session.commit()
        flash('Conexão atualizada.', 'success')
        return redirect(url_for('admin_sheets.list_sheets'))
    return render_template('admin/sheets/form.html', conn=conn, action='edit')


@bp.route('/<int:sheet_id>/delete', methods=['POST'])
@login_required
def delete_sheet(sheet_id):
    conn = SheetConnection.query.get_or_404(sheet_id)
    conn.is_active = False
    db.session.commit()
    flash('Conexão removida.', 'info')
    return redirect(url_for('admin_sheets.list_sheets'))


@bp.route('/api/<int:sheet_id>/preview')
@login_required
def api_preview(sheet_id):
    conn = SheetConnection.query.get_or_404(sheet_id)
    try:
        headers = get_headers(conn)
        rows = get_rows_preview(conn, 5)
        return jsonify({'headers': headers, 'rows': rows})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/api/<int:sheet_id>/rows')
@login_required
def api_rows(sheet_id):
    conn = SheetConnection.query.get_or_404(sheet_id)
    try:
        rows = get_all_rows(conn)
        return jsonify({'rows': rows, 'count': len(rows)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
