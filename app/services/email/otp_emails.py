from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail


def send_otp_code(sig_req, otp_code: str) -> None:
    subject = f'[{current_app.config["PLATFORM_NAME"]}] Seu código de verificação: {otp_code}'
    msg = Message(subject=subject, recipients=[sig_req.signatory_email])
    msg.html = render_template('email/otp_code.html',
                               sig_req=sig_req, code=otp_code,
                               platform=current_app.config['PLATFORM_NAME'])
    msg.body = render_template('email/otp_code.txt',
                               sig_req=sig_req, code=otp_code,
                               platform=current_app.config['PLATFORM_NAME'])
    mail.send(msg)
