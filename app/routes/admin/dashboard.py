from flask import Blueprint, render_template
from flask_login import login_required
from app.models.document import Document
from app.models.signature_request import SignatureRequest

bp = Blueprint('admin_dashboard', __name__, url_prefix='/admin')


@bp.route('/')
@login_required
def index():
    stats = {
        'total_documents': Document.query.count(),
        'pending': Document.query.filter_by(status='pending_signatures').count(),
        'partially_signed': Document.query.filter_by(status='partially_signed').count(),
        'completed': Document.query.filter_by(status='completed').count(),
        'pending_signatures': SignatureRequest.query.filter_by(status='pending').count(),
        'recent_documents': Document.query.order_by(Document.created_at.desc()).limit(10).all(),
    }
    return render_template('admin/dashboard.html', stats=stats)
