import pytest
from settings import create_app, db


@pytest.yield_fixture(scope='session')
def app():
    flask_app = create_app('testing')
    ctx = flask_app.app_context()
    ctx.push()
    yield flask_app
    ctx.pop()


@pytest.fixture(scope='session')
def client(app):
    yield app.test_client()


@pytest.yield_fixture(scope='module')
def init_db(app):
    db.create_all()
    yield db
    db.session.close()
    db.drop_all()
