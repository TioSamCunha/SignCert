"""Absolute path helpers for upload directories."""
import os
from flask import current_app


def abs_upload_path(relative_or_absolute: str) -> str:
    """
    Return an absolute path for an upload file.
    Relative paths are resolved from the project root (parent of app/).
    """
    if os.path.isabs(relative_or_absolute):
        return relative_or_absolute
    project_root = os.path.dirname(current_app.root_path)
    return os.path.normpath(os.path.join(project_root, relative_or_absolute))


def get_pdf_dir() -> str:
    d = current_app.config.get('GENERATED_PDFS_DIR', 'uploads/generated_pdfs')
    return abs_upload_path(d)


def get_images_dir() -> str:
    d = current_app.config.get('SIGNATURE_IMAGES_DIR', 'uploads/signature_images')
    return abs_upload_path(d)


def get_certs_dir() -> str:
    d = current_app.config.get('CERTIFICATES_DIR', 'uploads/certificates')
    return abs_upload_path(d)
