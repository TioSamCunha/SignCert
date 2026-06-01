def test_login_page_loads(client):
    resp = client.get('/auth/login')
    assert resp.status_code == 200
    assert b'SignCert' in resp.data


def test_setup_page_available_when_no_users(client):
    resp = client.get('/auth/setup')
    assert resp.status_code == 200


def test_login_invalid_credentials(client):
    resp = client.post('/auth/login', data={'email': 'x@x.com', 'password': 'wrong'})
    assert resp.status_code == 200


def test_dashboard_requires_auth(client):
    resp = client.get('/admin/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']
