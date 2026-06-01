import os
from flask import Flask
from config import config
from app.extensions import db, migrate, login_manager, mail, csrf


def create_app(config_name: str = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config.get(config_name, config['default']))

    _init_extensions(app)
    _register_blueprints(app)
    _register_shell_context(app)
    _ensure_upload_dirs(app)

    if config_name != 'testing':
        _start_scheduler(app)

    return app


def _start_scheduler(app: Flask) -> None:
    try:
        from app.scheduler import init_scheduler
        init_scheduler(app)
    except Exception:
        pass


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


def _register_blueprints(app: Flask) -> None:
    from app.routes.auth import bp as auth_bp
    from app.routes.admin.dashboard import bp as dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    # Remaining blueprints registered as implemented
    _register_admin_blueprints(app)
    _register_signing_blueprints(app)
    _register_public_blueprints(app)


def _register_admin_blueprints(app: Flask) -> None:
    try:
        from app.routes.admin.sheets import bp as sheets_bp
        app.register_blueprint(sheets_bp)
    except ImportError:
        pass
    try:
        from app.routes.admin.templates import bp as templates_bp
        app.register_blueprint(templates_bp)
    except ImportError:
        pass
    try:
        from app.routes.admin.documents import bp as documents_bp
        app.register_blueprint(documents_bp)
    except ImportError:
        pass
    try:
        from app.routes.admin.signatories import bp as signatories_bp
        app.register_blueprint(signatories_bp)
    except ImportError:
        pass
    try:
        from app.routes.admin.drive import bp as drive_bp
        app.register_blueprint(drive_bp)
    except ImportError:
        pass


def _register_signing_blueprints(app: Flask) -> None:
    try:
        from app.routes.signing.view import bp as signing_view_bp
        app.register_blueprint(signing_view_bp)
    except ImportError:
        pass
    try:
        from app.routes.signing.otp import bp as otp_bp
        app.register_blueprint(otp_bp)
    except ImportError:
        pass
    try:
        from app.routes.signing.submit import bp as submit_bp
        app.register_blueprint(submit_bp)
    except ImportError:
        pass
    try:
        from app.routes.signing.digital_cert import bp as digital_cert_bp
        app.register_blueprint(digital_cert_bp)
    except ImportError:
        pass


def _register_public_blueprints(app: Flask) -> None:
    try:
        from app.routes.public.verify import bp as verify_bp
        app.register_blueprint(verify_bp)
    except ImportError:
        pass


def _register_shell_context(app: Flask) -> None:
    from app import models

    @app.shell_context_processor
    def ctx():
        return {'db': db, **{m: getattr(models, m) for m in models.__all__}}


def _ensure_upload_dirs(app: Flask) -> None:
    for key in ('GENERATED_PDFS_DIR', 'SIGNATURE_IMAGES_DIR', 'CERTIFICATES_DIR'):
        path = app.config.get(key, '')
        if path:
            os.makedirs(path, exist_ok=True)
