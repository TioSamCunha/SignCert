import os
from flask import current_app, render_template
from app.services.certificate.builder import build_certificate_data
from app.services.pdf.renderer import html_to_pdf


def generate_certificate_pdf(document) -> str:
    data = build_certificate_data(document)
    qr_b64 = _build_qr(document.uuid)
    html = render_template('certificate/certificate.html',
                           cert=data, qr_b64=qr_b64)
    from app.utils.paths import get_certs_dir
    certs_dir = get_certs_dir()
    os.makedirs(certs_dir, exist_ok=True)
    path = os.path.join(certs_dir, f'cert_{document.id}.pdf')
    html_to_pdf(html, path)
    return path


def _build_qr(document_uuid: str) -> str:
    import qrcode
    import io
    import base64
    from flask import current_app
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
    url = f'{base_url}/verify/{document_uuid}'
    qr = qrcode.make(url)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()
