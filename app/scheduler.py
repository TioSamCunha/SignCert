"""
APScheduler setup for background tasks:
- Expire overdue signature request tokens (every hour)
- Send reminder emails to pending signatories (every 6 hours)
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

_scheduler = None


def init_scheduler(app) -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        func=lambda: _expire_tokens(app),
        trigger=IntervalTrigger(hours=1),
        id='expire_tokens',
        replace_existing=True,
    )
    _scheduler.add_job(
        func=lambda: _send_reminders(app),
        trigger=IntervalTrigger(hours=6),
        id='send_reminders',
        replace_existing=True,
    )
    _scheduler.start()


def _expire_tokens(app) -> None:
    from datetime import datetime, timezone
    with app.app_context():
        from app.extensions import db
        from app.models.signature_request import SignatureRequest
        expired = SignatureRequest.query.filter(
            SignatureRequest.status.in_(['pending', 'link_opened', 'otp_sent']),
            SignatureRequest.token_expires_at < datetime.now(timezone.utc),
        ).all()
        for sr in expired:
            sr.status = 'expired'
            import app.services.audit_service as audit
            audit.log('TOKEN_EXPIRED', document_id=sr.document_id,
                      signature_request_id=sr.id, actor_email='sistema')
        if expired:
            db.session.commit()


def _send_reminders(app) -> None:
    with app.app_context():
        from app.services.email.reminders import send_pending_reminders
        try:
            send_pending_reminders()
        except Exception:
            pass
