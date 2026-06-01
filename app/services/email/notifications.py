import logging
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)


def send_completion_notification(document, admin_email: str) -> None:
    if current_app.config.get('MAIL_SUPPRESS_SEND', True):
        logger.warning(f'\n>>> DOCUMENTO COMPLETO: {document.title} (UUID: {document.uuid}) <<<')
        return
    subject = f'[{current_app.config["PLATFORM_NAME"]}] Documento assinado: {document.title}'
    msg = Message(subject=subject, recipients=[admin_email])
    msg.html = render_template('email/document_completed.html',
                               document=document,
                               platform=current_app.config['PLATFORM_NAME'])
    msg.body = f'O documento "{document.title}" foi completamente assinado.\nUUID: {document.uuid}'
    mail.send(msg)


def send_signed_notification(document, sig_req, admin_email: str) -> None:
    if current_app.config.get('MAIL_SUPPRESS_SEND', True):
        logger.warning(f'\n>>> NOTIF: {sig_req.signatory_name} assinou "{document.title}" <<<')
        return
    subject = f'[{current_app.config["PLATFORM_NAME"]}] {sig_req.signatory_name} assinou: {document.title}'
    msg = Message(subject=subject, recipients=[admin_email])
    msg.body = (f'{sig_req.signatory_name} ({sig_req.signatory_email}) '
                f'assinou o documento "{document.title}".')
    try:
        mail.send(msg)
    except Exception:
        pass
