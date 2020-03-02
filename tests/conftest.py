import pytest
from unittest.mock import Mock
from settings import create_app

from api.models import Unit, Membership, db, Invitation, Role, Parameter, ApplianceCategory
from .mocks import (ApplianceCategoryGenerator, OrganisationGenerator,
                    UserGenerator, ParameterGenerator)
from seeders.seeders_manager import SeederManager


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
    from .mocks.redis import RedisMock
    db.create_all()
    SeederManager.run()
    RedisMock.flush_all()
    yield db
    db.session.close()
    db.drop_all()


@pytest.fixture(scope='module')
def bulk_create_unit_objects(init_db, unit_objs):
    return Unit.bulk_create(unit_objs)


@pytest.fixture(scope='session')
def save_appliance_category_to_org():
    def _inner_func(num_of_obs=3, org=None):
        if not org:
            org = OrganisationGenerator.generate_model_obj(save=True)
        model_onjs = [
            ApplianceCategoryGenerator.generate_model_obj(org.id, save=False)
            for _ in range(0, num_of_obs)
        ]

        model_objs = ApplianceCategory.bulk_create(model_onjs)

        return model_objs, org

    return _inner_func


@pytest.fixture(scope='function')
def saved_org_and_user_generator(unit_objs):
    user_obj = UserGenerator.generate_model_obj(save=True, verified=True)
    org = OrganisationGenerator.generate_model_obj(user_obj.id, save=True)
    return user_obj, org


@pytest.fixture(scope='function')
def saved_user_invitations(init_db):
    def create_and_return_mock_data(num_of_org=3,
                                    role_name='REGULAR USERS',
                                    user=None):
        org_objs = []
        for _ in range(0, num_of_org):
            org_objs.append(
                OrganisationGenerator.generate_model_obj(save=True))

        if not user:
            user = UserGenerator.generate_model_obj(save=True, verified=True)
        regular_user_id = Role.query.filter_by(name=role_name).first().id
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
def saved_parameters_to_org(init_db):
    def create_and_return_mock_data(num_of_params=3, org=None, unit_id=None):
        if not org:
            org = OrganisationGenerator.generate_model_obj(save=True)
        params_objs = [
            ParameterGenerator.generate_model_obj(organisation_id=org.id,
                                                  save=False,
                                                  unit_id=unit_id)
            for _ in range(0, num_of_params)
        ]

        params_objs = Parameter.bulk_create(params_objs)

        return params_objs, org

    return create_and_return_mock_data


@pytest.fixture(scope='function')
def add_user_to_organisation(init_db):
    def _add_user_to_organisation(org, user, role='REGULAR USERS'):
        role_obj = Role.query.filter_by(name=role).first()
        Membership(organisation_id=org.id,
                   user_id=user.id,
                   role_id=role_obj.id).save()

    return _add_user_to_organisation


@pytest.fixture(scope='function')
def mock_send_html_delay():
    from api.utils.emails import EmailUtil
    EmailUtil.send_mail_as_html.delay = Mock(
        side_effect=EmailUtil.send_mail_as_html)
    return EmailUtil.send_mail_as_html.delay


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
