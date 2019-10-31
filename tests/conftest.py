import pytest
from settings import create_app, db
from api.models import Unit
from .mocks.organisation import OrganisationGenerator
from .mocks.user import UserGenerator


@pytest.yield_fixture(scope='session')
def app():
    flask_app = create_app('testing')
    ctx = flask_app.app_context()
    ctx.push()
    yield flask_app
    ctx.pop()


@pytest.fixture(scope='function')
def client(app):
    yield app.test_client()


@pytest.fixture(scope='session')
def unit_objs(app):
    return [
        dict(letter_symbol='A', name='Ampere'),
        dict(letter_symbol='J', name='Joules'),
        dict(letter_symbol='Hz', name='Hertz'),
        dict(letter_symbol='N', name='Newton'),
        dict(letter_symbol='atm', name='Atmosphere'),
        dict(letter_symbol='m', name='Meters'),
        dict(letter_symbol='Cal', name='Calories'),
        dict(letter_symbol='V', name='Voltage'),
        dict(greek_symbol_num=48, name='Ohm'),
        dict(letter_symbol='yd', name='Yards'),
        dict(letter_symbol='in', name='Inches'),
        dict(letter_symbol='ft', name='Feet'),
        dict(letter_symbol='db', name='Decibels'),
    ]


@pytest.yield_fixture(scope='module')
def init_db(app):
    db.create_all()
    yield db
    db.session.close()
    db.drop_all()


@pytest.fixture(scope='module')
def bulk_create_unit_objects(init_db, unit_objs):
    return Unit.bulk_create(unit_objs)


@pytest.fixture(scope='function')
def saved_org_and_user_generator(unit_objs):
    user_obj = UserGenerator.generate_model_obj(save=True, verified=True)
    org = OrganisationGenerator.generate_model_obj(user_obj.id, save=True)
    return user_obj, org
