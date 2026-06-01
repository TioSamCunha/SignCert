import logging
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)


def send_otp_code(sig_req, otp_code: str) -> None:
    subject = f'[{current_app.config["PLATFORM_NAME"]}] Seu codigo de verificacao: {otp_code}'

    # Sempre loga no terminal (visivel no modo dev)
    logger.warning(
        f'\n>>> OTP para {sig_req.signatory_email}: {otp_code} <<<'
    )

    if current_app.config.get('MAIL_SUPPRESS_SEND', True):
        return  # Modo dev: nao envia, so loga

    msg = Message(subject=subject, recipients=[sig_req.signatory_email])
    msg.html = render_template('email/otp_code.html',
                               sig_req=sig_req, code=otp_code,
                               platform=current_app.config['PLATFORM_NAME'])
    msg.body = render_template('email/otp_code.txt',
                               sig_req=sig_req, code=otp_code,
                               platform=current_app.config['PLATFORM_NAME'])
    mail.send(msg)
