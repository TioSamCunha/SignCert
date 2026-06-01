import base64
import os
from app.utils.formatters import to_brasilia, format_cpf


def build_certificate_data(document) -> dict:
    sig_requests = document.signature_requests.all()
    signatories = []
    for sr in sig_requests:
        sig_img_b64 = None
        if sr.signature_image_path and os.path.exists(sr.signature_image_path):
            with open(sr.signature_image_path, 'rb') as f:
                sig_img_b64 = base64.b64encode(f.read()).decode()
        signatories.append({
            'name': sr.signatory_name,
            'email': sr.signatory_email,
            'cpf': format_cpf(sr.signatory_cpf) if sr.signatory_cpf else 'Não informado',
            'signature_img_b64': sig_img_b64,
            'signature_type': 'Manuscrita digitalizada' if sr.signature_type == 'drawn' else 'Digitada',
            'method': sr.method,
            'otp_verified_at': to_brasilia(sr.otp_verified_at),
            'signed_at': to_brasilia(sr.signed_at),
            'ip_address': sr.ip_address or '-',
            'location': _format_location(sr),
            'user_agent': (sr.user_agent or '-')[:200],
            'document_hash_at_signing': sr.document_hash_at_signing or '-',
        })
    return {
        'document_uuid': document.uuid,
        'document_title': document.title,
        'sha256_draft': document.sha256_draft_hash or '-',
        'sha256_final': document.sha256_hash or 'Pendente',
        'created_at': to_brasilia(document.created_at),
        'completed_at': to_brasilia(document.completed_at),
        'signatories': signatories,
        'total_signatories': len(signatories),
    }


def _format_location(sr) -> str:
    parts = [p for p in [sr.geolocation_city, sr.geolocation_region, sr.geolocation_country] if p]
    return ', '.join(parts) if parts else '-'
