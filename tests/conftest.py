import pytest
from settings import create_app
from api.models import Unit
from .mocks.organisation import OrganisationGenerator
from .mocks.user import UserGenerator
from seeders.seeders_manager import SeederManager
from .mocks.redis import RedisMock
from api.models import Role, Invitation, db


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
    SeederManager.seed_database('role')
    RedisMock.flush_all()
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


@pytest.fixture(scope='function')
def saved_user_invitations(init_db):
    def create_and_return_mock_data(num_of_org=3):
        org_objs = []
        for _ in range(0, num_of_org):
            org_objs.append(
                OrganisationGenerator.generate_model_obj(save=True))

        user = UserGenerator.generate_model_obj(save=True, verified=True)
        regular_user_id = Role.query.filter_by(name='REGULAR USERS').first().id
        invitations = []
        org_ids = set(org.id for org in org_objs)
        for org in org_objs:
            invitations.append(
                Invitation(
                    organisation_id=org.id,
                    email=user.email,
                    role_id=regular_user_id,
                    user_dashboard_url='http://some_url',
                    signup_url='http://some_url',
                ))

        Invitation.bulk_create(invitations)
        return org_objs, user, org_ids, invitations, regular_user_id

    return create_and_return_mock_data


@pytest.fixture(scope='function')
def saved_organisation_invitations(init_db):
    def create_and_return_mock_data(num_of_org=3):
        user_objs = []
        for _ in range(0, num_of_org):
            user_objs.append(
                UserGenerator.generate_model_obj(save=True, verified=True))

        org = OrganisationGenerator.generate_model_obj(save=True)
        regular_user_id = Role.query.filter_by(name='REGULAR USERS').first().id
        invitations = []
        user_ids = set(user.id for user in user_objs)
        for user in user_objs:
            invitations.append(
                Invitation(
                    organisation_id=org.id,
                    email=user.email,
                    role_id=regular_user_id,
                    user_dashboard_url='http://some_url',
                    signup_url='http://some_url',
                ))

        Invitation.bulk_create(invitations)
        return user_objs, org, user_ids, invitations, regular_user_id

    return create_and_return_mock_data
