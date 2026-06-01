import os
from googleapiclient.http import MediaFileUpload
from app.extensions import db
from app.services.drive.connector import get_drive_service
import app.services.audit_service as audit


def upload_final_pdf(document) -> dict | None:
    from app.models.drive_config import DriveConfig
    config = DriveConfig.query.filter_by(is_active=True).first()
    if not config:
        return None
    if not document.pdf_path or not os.path.exists(document.pdf_path):
        return None
    service = get_drive_service(config)
    file_name = f'{document.uuid}_{document.title}_assinado.pdf'
    metadata = {'name': file_name, 'mimeType': 'application/pdf'}
    if config.folder_id:
        metadata['parents'] = [config.folder_id]
    media = MediaFileUpload(document.pdf_path, mimetype='application/pdf')
    uploaded = service.files().create(
        body=metadata, media_body=media, fields='id,webViewLink').execute()
    document.drive_file_id = uploaded.get('id')
    document.drive_file_url = uploaded.get('webViewLink')
    db.session.commit()
    audit.log('DRIVE_UPLOADED', document_id=document.id,
              actor_email='sistema',
              details={'drive_file_id': document.drive_file_id})
    return uploaded
