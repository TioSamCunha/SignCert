import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()


@pytest.fixture(scope='function')
def admin_user(db):
    from app.models.user import User
    u = User(email='admin@test.com', full_name='Admin Test', is_superadmin=True)
    u.set_password('password123')
    db.session.add(u)
    db.session.commit()
    return u
