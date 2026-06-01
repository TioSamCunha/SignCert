"""Tests for public document verification route."""
import hashlib
import pytest
from unittest.mock import patch


def test_verify_nonexistent_uuid(client):
    resp = client.get('/verify/00000000-0000-0000-0000-000000000000')
    assert resp.status_code == 200
    assert 'não encontrado' in resp.data.decode('utf-8')


def test_verify_page_loads_with_invalid_uuid(client):
    resp = client.get('/verify/invalid-uuid-here')
    assert resp.status_code == 200


def test_verify_existing_document_no_pdf(client, db, sample_doc):
    sample_doc.pdf_path = None
    db.session.commit()
    resp = client.get(f'/verify/{sample_doc.uuid}')
    assert resp.status_code == 200
    assert sample_doc.title.encode() in resp.data


def test_verify_existing_document_hash_mismatch(client, db, sample_doc, tmp_path):
    f = tmp_path / 'doc.pdf'
    f.write_bytes(b'%PDF-1.4 fake content')
    sample_doc.pdf_path = str(f)
    sample_doc.sha256_hash = 'wronghashvalue'
    db.session.commit()
    with patch('app.utils.paths.abs_upload_path', return_value=str(f)):
        resp = client.get(f'/verify/{sample_doc.uuid}')
    assert resp.status_code == 200


def test_verify_existing_document_hash_match(client, db, sample_doc, tmp_path):
    content = b'%PDF-1.4 real signed content'
    f = tmp_path / 'final.pdf'
    f.write_bytes(content)
    sample_doc.pdf_path = str(f)
    sample_doc.sha256_hash = hashlib.sha256(content).hexdigest()
    db.session.commit()
    with patch('app.utils.paths.abs_upload_path', return_value=str(f)):
        resp = client.get(f'/verify/{sample_doc.uuid}')
    assert resp.status_code == 200


def test_verify_qr_route_same_as_verify(client, db, sample_doc):
    resp_verify = client.get(f'/verify/{sample_doc.uuid}')
    resp_qr = client.get(f'/verify/qr/{sample_doc.uuid}')
    assert resp_verify.status_code == resp_qr.status_code


def test_download_certificate_not_found_when_no_pdf(client, db, sample_doc):
    sample_doc.pdf_path = None
    db.session.commit()
    resp = client.get(f'/verify/{sample_doc.uuid}/download')
    assert resp.status_code == 404


def test_download_certificate_file_missing_on_disk(client, db, sample_doc, tmp_path):
    sample_doc.pdf_path = str(tmp_path / 'nonexistent.pdf')
    db.session.commit()
    with patch('app.utils.paths.abs_upload_path', return_value=str(tmp_path / 'nonexistent.pdf')):
        resp = client.get(f'/verify/{sample_doc.uuid}/download')
    assert resp.status_code == 404


def test_download_certificate_success(client, db, sample_doc, tmp_path):
    f = tmp_path / 'signed.pdf'
    f.write_bytes(b'%PDF-1.4 signed')
    sample_doc.pdf_path = str(f)
    db.session.commit()
    with patch('app.utils.paths.abs_upload_path', return_value=str(f)):
        resp = client.get(f'/verify/{sample_doc.uuid}/download')
    assert resp.status_code == 200
    assert resp.content_type == 'application/pdf'
