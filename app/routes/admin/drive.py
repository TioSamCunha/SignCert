from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.drive_config import DriveConfig
from app.services.sheets.connector import encrypt_credentials
from app.services.drive.connector import check_drive_connection

bp = Blueprint('admin_drive', __name__, url_prefix='/admin/drive')


@bp.route('/')
@login_required
def index():
    config = DriveConfig.query.filter_by(is_active=True).first()
    return render_template('admin/drive/index.html', config=config)


@bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    if request.method == 'POST':
        creds_json = request.form.get('service_account_json', '').strip()
        folder_id = request.form.get('folder_id', '').strip() or None
        ok, msg = check_drive_connection(creds_json, folder_id)
        if not ok:
            flash(msg, 'danger')
            return render_template('admin/drive/setup.html')
        existing = DriveConfig.query.filter_by(is_active=True).first()
        if existing:
            existing.service_account_json = encrypt_credentials(creds_json)
            existing.folder_id = folder_id
            existing.display_name = request.form.get('display_name', 'Google Drive').strip()
        else:
            config = DriveConfig(
                user_id=current_user.id,
                display_name=request.form.get('display_name', 'Google Drive').strip(),
                service_account_json=encrypt_credentials(creds_json),
                folder_id=folder_id,
            )
            db.session.add(config)
        db.session.commit()
        flash('Google Drive configurado com sucesso.', 'success')
        return redirect(url_for('admin_drive.index'))
    return render_template('admin/drive/setup.html')


@bp.route('/disable', methods=['POST'])
@login_required
def disable():
    DriveConfig.query.filter_by(is_active=True).update({'is_active': False})
    db.session.commit()
    flash('Integração com Google Drive desativada.', 'info')
    return redirect(url_for('admin_drive.index'))
