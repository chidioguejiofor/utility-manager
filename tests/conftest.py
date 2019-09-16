import pytest
from settings import create_app, db
from tests.mocks.organisation import valid_org_dict
from tests.mocks.user import valid_user_one_dict
from api.models import Organisation, User


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


@pytest.fixture(scope='module')
def valid_organisation(app):
    org = Organisation(**valid_org_dict)
    return org


@pytest.fixture(scope='module')
def valid_user_obj(app):
    user = User(**valid_user_one_dict)
    return user
