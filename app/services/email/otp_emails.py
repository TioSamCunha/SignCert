import logging
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)


def send_otp_code(sig_req, otp_code: str) -> None:
    subject = f'[{current_app.config["PLATFORM_NAME"]}] Seu código de verificação: {otp_code}'
    msg = Message(subject=subject, recipients=[sig_req.signatory_email])
    msg.html = render_template('email/otp_code.html',
                               sig_req=sig_req, code=otp_code,
                               platform=current_app.config['PLATFORM_NAME'])
    msg.body = render_template('email/otp_code.txt',
                               sig_req=sig_req, code=otp_code,
                               platform=current_app.config['PLATFORM_NAME'])

    if current_app.config.get('FLASK_DEBUG') or current_app.debug:
        logger.warning(
            '\n'
            '╔══════════════════════════════════════╗\n'
            '║  OTP CODE (modo dev — não enviado)   ║\n'
            f'║  Destinatário : {sig_req.signatory_email:<22}║\n'
            f'║  CÓDIGO       : {otp_code:<22}║\n'
            '╚══════════════════════════════════════╝'
        )

    try:
        mail.send(msg)
    except Exception as e:
        logger.error(f'Falha ao enviar e-mail OTP para {sig_req.signatory_email}: {e}')
        if not (current_app.config.get('FLASK_DEBUG') or current_app.debug):
            raise
