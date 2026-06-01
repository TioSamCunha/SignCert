"""Tests for authentication routes and user model."""
import pytest


def test_login_page_loads(client):
    resp = client.get('/auth/login')
    assert resp.status_code == 200
    assert b'SignCert' in resp.data


def test_setup_page_available_when_no_users(client, db):
    from app.models.user import User
    # ensure no users exist
    User.query.delete()
    db.session.commit()
    resp = client.get('/auth/setup')
    assert resp.status_code == 200


def test_setup_redirects_when_admin_exists(client, admin_user):
    resp = client.get('/auth/setup', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_setup_creates_admin(client, db):
    from app.models.user import User
    User.query.delete()
    db.session.commit()

    resp = client.post('/auth/setup', data={
        'email': 'novo@admin.com',
        'full_name': 'Novo Admin',
        'password': 'senha12345',
    }, follow_redirects=False)
    assert resp.status_code == 302

    user = User.query.filter_by(email='novo@admin.com').first()
    assert user is not None
    assert user.is_superadmin is True
    assert user.check_password('senha12345')


def test_login_invalid_credentials(client, admin_user):
    resp = client.post('/auth/login', data={
        'email': admin_user.email,
        'password': 'senhaerrada',
    })
    assert resp.status_code == 200
    assert 'inválidos' in resp.data.decode('utf-8') or b'E-mail' in resp.data


def test_login_success_redirects_to_dashboard(client, admin_user):
    resp = client.post('/auth/login', data={
        'email': admin_user.email,
        'password': 'password123',
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert '/admin' in resp.headers['Location']


def test_login_updates_last_login_at(client, db, admin_user):
    assert admin_user.last_login_at is None
    client.post('/auth/login', data={
        'email': admin_user.email,
        'password': 'password123',
    })
    db.session.refresh(admin_user)
    assert admin_user.last_login_at is not None


def test_dashboard_requires_auth(client):
    resp = client.get('/admin/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_logout_redirects_to_login(logged_in_client):
    resp = logged_in_client.get('/auth/logout', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_already_authenticated_login_redirects(client, admin_user):
    # First login
    client.post('/auth/login', data={
        'email': admin_user.email,
        'password': 'password123',
    })
    # Second login attempt should redirect to dashboard
    resp = client.get('/auth/login', follow_redirects=False)
    assert resp.status_code == 302
