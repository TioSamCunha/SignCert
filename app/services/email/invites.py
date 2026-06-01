from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail


def send_signing_invitation(sig_req, signing_url: str) -> None:
    subject = f'[{current_app.config["PLATFORM_NAME"]}] Documento aguarda sua assinatura'
    msg = Message(subject=subject, recipients=[sig_req.signatory_email])
    msg.html = render_template('email/signing_invite.html',
                               sig_req=sig_req, signing_url=signing_url,
                               platform=current_app.config['PLATFORM_NAME'])
    msg.body = render_template('email/signing_invite.txt',
                               sig_req=sig_req, signing_url=signing_url,
                               platform=current_app.config['PLATFORM_NAME'])
    mail.send(msg)
