import os
from datetime import datetime, timezone
from flask import current_app
from app.extensions import db
from app.models.document import Document
from app.models.signature_request import SignatureRequest
from app.services.pdf.merger import merge_pdfs
from app.services.pdf.hasher import sha256_file
import app.services.audit_service as audit


def check_all_signed(document_id: int) -> bool:
    reqs = SignatureRequest.query.filter_by(document_id=document_id).all()
    return reqs and all(r.status == 'signed' for r in reqs)


def finalize_document(document_id: int) -> Document:
    doc = Document.query.get(document_id)
    cert_path = _build_certificate(doc)
    final_path = _merge_final(doc, cert_path)
    doc.pdf_path = final_path
    doc.sha256_hash = sha256_file(final_path)
    doc.status = 'completed'
    doc.completed_at = datetime.now(timezone.utc)
    db.session.commit()
    audit.log('DOCUMENT_COMPLETED', document_id=document_id,
              actor_email='sistema', details={'sha256': doc.sha256_hash})
    _try_drive_upload(doc)
    return doc


def _build_certificate(doc: Document) -> str:
    from app.services.certificate.renderer import generate_certificate_pdf
    return generate_certificate_pdf(doc)


def _merge_final(doc: Document, cert_path: str) -> str:
    from app.utils.paths import get_pdf_dir, abs_upload_path
    pdf_dir = get_pdf_dir()
    output_path = os.path.join(pdf_dir, f'doc_{doc.id}_final.pdf')
    draft = abs_upload_path(doc.draft_pdf_path)
    return merge_pdfs(draft, cert_path, output_path)


def _try_drive_upload(doc: Document) -> None:
    try:
        from app.services.drive.uploader import upload_final_pdf
        upload_final_pdf(doc)
    except Exception:
        pass
