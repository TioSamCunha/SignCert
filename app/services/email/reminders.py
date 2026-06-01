"""
Automated reminder emails for pending signature requests.
Runs via APScheduler — called from the scheduler setup.
"""
from datetime import datetime, timezone, timedelta
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail, db
from app.models.signature_request import SignatureRequest
import app.services.audit_service as audit


def send_pending_reminders() -> int:
    """
    Send reminder emails to signatories whose requests are still pending
    and expire within the next 24 hours. Returns count of reminders sent.
    """
    from flask import url_for
    app = current_app._get_current_object()
    with app.app_context():
        cutoff_soon = datetime.now(timezone.utc) + timedelta(hours=24)
        cutoff_past = datetime.now(timezone.utc)
        pending = SignatureRequest.query.filter(
            SignatureRequest.status.in_(['pending', 'link_opened']),
            SignatureRequest.token_expires_at > cutoff_past,
            SignatureRequest.token_expires_at <= cutoff_soon,
        ).all()
        sent = 0
        for sr in pending:
            try:
                signing_url = url_for('signing_view.sign', token=sr.token, _external=True)
                _send_reminder(sr, signing_url)
                audit.log('REMINDER_SENT', document_id=sr.document_id,
                          signature_request_id=sr.id,
                          actor_email='sistema',
                          details={'hours_remaining': round(
                              (sr.token_expires_at.replace(tzinfo=timezone.utc)
                               - datetime.now(timezone.utc)).total_seconds() / 3600, 1)})
                sent += 1
            except Exception:
                pass
        return sent


def _send_reminder(sig_req, signing_url: str) -> None:
    platform = current_app.config.get('PLATFORM_NAME', 'SignCert')
    subject = f'[{platform}] Lembrete: documento aguarda sua assinatura'
    msg = Message(subject=subject, recipients=[sig_req.signatory_email])
    msg.html = render_template('email/reminder.html',
                               sig_req=sig_req, signing_url=signing_url,
                               platform=platform)
    msg.body = (f'Olá {sig_req.signatory_name},\n\n'
                f'Lembramos que o documento "{sig_req.document.title}" '
                f'ainda aguarda sua assinatura.\n\nLink: {signing_url}\n\n'
                f'Este link expira em breve.')
    mail.send(msg)
