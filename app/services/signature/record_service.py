import base64
import os
import re
from datetime import datetime, timezone
from flask import current_app
from app.extensions import db
from app.models.signature_request import SignatureRequest


def save_signature_image(signature_request_id: int, data_url: str) -> str:
    match = re.match(r'data:image/png;base64,(.+)', data_url)
    if not match:
        raise ValueError('Invalid signature data URL')
    img_data = base64.b64decode(match.group(1))
    if len(img_data) < 100:
        raise ValueError('Signature image is too small (blank)')
    images_dir = current_app.config.get('SIGNATURE_IMAGES_DIR', 'uploads/signature_images')
    os.makedirs(images_dir, exist_ok=True)
    path = os.path.join(images_dir, f'sig_{signature_request_id}.png')
    with open(path, 'wb') as f:
        f.write(img_data)
    return path


def record_signature(sig_req: SignatureRequest, data_url: str,
                     sig_type: str, ip: str, user_agent: str,
                     document_hash: str) -> None:
    sig_req.signature_image_path = save_signature_image(sig_req.id, data_url)
    sig_req.signature_type = sig_type
    sig_req.document_hash_at_signing = document_hash
    sig_req.signed_at = datetime.now(timezone.utc)
    sig_req.status = 'signed'
    db.session.commit()
