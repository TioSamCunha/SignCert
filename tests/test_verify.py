"""Tests for the public document verification endpoint."""
import pytest
from app.models.document import Document


def test_verify_nonexistent_uuid(client, db):
    resp = client.get('/verify/00000000-0000-0000-0000-000000000000')
    assert resp.status_code in (200, 404)


def test_verify_page_loads(client, db):
    resp = client.get('/verify/invalid-uuid')
    assert resp.status_code in (200, 404)
