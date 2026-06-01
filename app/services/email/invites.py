import logging
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)


def send_signing_invitation(sig_req, signing_url: str) -> None:
    subject = f'[{current_app.config["PLATFORM_NAME"]}] Documento aguarda sua assinatura'

    # Sempre loga no terminal
    logger.warning(
        f'\n>>> LINK DE ASSINATURA para {sig_req.signatory_email}:\n    {signing_url} <<<'
    )

    if current_app.config.get('MAIL_SUPPRESS_SEND', True):
        return  # Modo dev: nao envia, so loga

    msg = Message(subject=subject, recipients=[sig_req.signatory_email])
    msg.html = render_template('email/signing_invite.html',
                               sig_req=sig_req, signing_url=signing_url,
                               platform=current_app.config['PLATFORM_NAME'])
    msg.body = render_template('email/signing_invite.txt',
                               sig_req=sig_req, signing_url=signing_url,
                               platform=current_app.config['PLATFORM_NAME'])
    mail.send(msg)
