"""
OTP delivery via SMS using Twilio.
Falls back gracefully if Twilio is not configured.
"""
from flask import current_app


def send_otp_sms(phone_number: str, otp_code: str, platform_name: str) -> tuple[bool, str]:
    """
    Send OTP code via SMS. Returns (success, message).
    """
    sid = current_app.config.get('TWILIO_ACCOUNT_SID', '')
    token = current_app.config.get('TWILIO_AUTH_TOKEN', '')
    from_number = current_app.config.get('TWILIO_FROM_NUMBER', '')
    if not all([sid, token, from_number]):
        return False, 'Twilio não configurado. Configure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN e TWILIO_FROM_NUMBER.'
    try:
        from twilio.rest import Client
        client = Client(sid, token)
        body = f'[{platform_name}] Seu código de verificação: {otp_code}. Válido por 10 minutos.'
        message = client.messages.create(to=phone_number, from_=from_number, body=body)
        return True, f'SMS enviado (SID: {message.sid})'
    except ImportError:
        return False, 'Biblioteca twilio não instalada. Execute: pip install twilio'
    except Exception as e:
        return False, f'Erro ao enviar SMS: {str(e)}'
