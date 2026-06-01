from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
import app.services.audit_service as audit

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            user.last_login_at = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user, remember=request.form.get('remember') == 'on')
            audit.log('LOGIN', user_id=user.id, actor_email=user.email,
                      ip=request.remote_addr, user_agent=request.user_agent.string)
            return redirect(request.args.get('next') or url_for('admin.dashboard.index'))
        flash('E-mail ou senha inválidos.', 'danger')
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    audit.log('LOGOUT', user_id=current_user.id, actor_email=current_user.email)
    logout_user()
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/setup', methods=['GET', 'POST'])
def setup():
    if User.query.count() > 0:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        user = User(
            email=request.form['email'].strip().lower(),
            full_name=request.form['full_name'].strip(),
            is_superadmin=True,
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Administrador criado com sucesso. Faça login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/setup.html')
