import logging
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)


def send_signing_invitation(sig_req, signing_url: str) -> None:
    subject = f'[{current_app.config["PLATFORM_NAME"]}] Documento aguarda sua assinatura'
    msg = Message(subject=subject, recipients=[sig_req.signatory_email])
    msg.html = render_template('email/signing_invite.html',
                               sig_req=sig_req, signing_url=signing_url,
                               platform=current_app.config['PLATFORM_NAME'])
    msg.body = render_template('email/signing_invite.txt',
                               sig_req=sig_req, signing_url=signing_url,
                               platform=current_app.config['PLATFORM_NAME'])

    if current_app.config.get('FLASK_DEBUG') or current_app.debug:
        logger.warning(
            '\n'
            '╔══════════════════════════════════════════════════════╗\n'
            '║  CONVITE DE ASSINATURA (modo dev — não enviado)      ║\n'
            f'║  Destinatário : {sig_req.signatory_email:<38}║\n'
            f'║  Link         : {signing_url:<38}║\n'
            '╚══════════════════════════════════════════════════════╝'
        )

    try:
        mail.send(msg)
    except Exception as e:
        logger.error(f'Falha ao enviar convite para {sig_req.signatory_email}: {e}')
        if not (current_app.config.get('FLASK_DEBUG') or current_app.debug):
            raise
