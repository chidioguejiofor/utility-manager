import json
from api.models import (
    Unit,
    ValueTypeEnum,
    Membership,
    db,
    Role,
    Parameter,
)
from api.utils.error_messages import serialization_error, parameter_errors, authentication_errors
from api.utils.success_messages import CREATED, RETRIEVED
from .mocks.user import UserGenerator
from .assertions import add_cookie_to_client, assert_paginator_data_values
PARAMETER_ENDPOINTS = '/api/org/{}/parameters'


def run_test_precondition(clear_params_only=True):
    Parameter.query.delete()
    db.session.commit()


class TestCreateParameterEndpointWithoutValidation:
    def test_should_create_parameter_when_valid_data_is_sent_to_body(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.NUMERIC.name,
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 201
        assert response_body['data']['name'] == parameter_json['name']
        assert response_body['data']['unit']['id'] == parameter_json['unitId']
        assert response_body['data']['createdAt'] is not None
        assert response_body['message'] == CREATED.format('Parameter')
        assert response_body['data']['editable'] is True

    def test_should_fail_when_user_is_not_part_of_organisation(
            self, app, init_db, client, bulk_create_unit_objects,
            saved_org_and_user_generator):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        user_two_ = UserGenerator.generate_model_obj(save=True, verified=True)
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.NUMERIC.name,
        }
        token = UserGenerator.generate_token(user_two_)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'not_found'].format('Organisation')
        assert response.status_code == 404

    def test_should_not_create_if_the_user_is_not_an_admin_in_any_organisation(
            self, app, init_db, client, bulk_create_unit_objects,
            saved_org_and_user_generator):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        user_two_ = UserGenerator.generate_model_obj(save=True, verified=True)
        Membership(user_id=user_two_.id,
                   organisation_id=org.id,
                   role_id=Role.query.filter_by(
                       name='REGULAR USERS').one().id).save()
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.NUMERIC.name,
        }
        token = UserGenerator.generate_token(user_two_)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response_body['message'] == authentication_errors[
            'forbidden'].format('create a parameter')
        assert response.status_code == 403

    def test_should_fail_when_data_is_missing(self, app, init_db, client,
                                              saved_org_and_user_generator):
        run_test_precondition()
        user, org = saved_org_and_user_generator

        parameter_json = {}
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['errors']['name'][
            0] == 'Missing data for required field.'
        assert response_body['message'] == serialization_error[
            'invalid_field_data']


class TestCreateParameterEndpointWithValidation:
    def test_if_value_type_is_numeric_and_validation_checks_numbers_then_parameter_should_be_created(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.NUMERIC.name,
            'validation': '  gte 20,    gt 50'
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 201
        assert response_body['data']['name'] == parameter_json['name']
        assert response_body['data']['unit']['id'] == parameter_json['unitId']
        assert response_body['data']['createdAt'] is not None
        assert response_body['message'] == CREATED.format('Parameter')
        assert response_body['data']['editable'] is True
        assert response_body['data']['validation'] == 'gte 20,gt 50'

    def test_should_throw_error_when_value_type_is_numeric_and_validation_is_not_for_numbers(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.NUMERIC.name,
            'validation': '  gte 2001-10-2,    gt 5001-20-9'
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == parameter_errors[
            'value_not_a_number'].format('2001-10-2', 'gte 2001-10-2')

    def test_should_throw_error_when_value_type_is_numeric_and_validation_is_more_than_4(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.NUMERIC.name,
            'validation': '  lt 22,    gt 50,  gte 30,    gt 90, gt 90'
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == parameter_errors[
            'invalid_validations']

    def test_should_fail_when_multiple_values_are_provided_for_numeric_type_validation(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.NUMERIC.name,
            'validation': 'lt 22 50'
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == parameter_errors[
            'invalid_validation_format'].format('lt 22 50')

    def test_should_fail_when_multiple_validation_type_eg_gte_is_provided_more_than_once(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.NUMERIC.name,
            'validation': 'lt 22, gte 30, gte 50'
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == parameter_errors[
            'multiple_validation_for_key'].format('gte')

    def test_should_fail_when_validation_type_is_numeric_and_key_is_invalid(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.NUMERIC.name,
            'validation': 'aba 50'
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == parameter_errors[
            'invalid_validation_key'].format('aba')

    def test_should_throw_error_when_value_type_is_date_and_validation_value_is_number(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.DATE.name,
            'validation': 'gte 5001'
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == parameter_errors[
            'number_not_a_date'].format('DATE', 'gte 5001')

    def test_should_throw_error_when_validation_is_date_and_value_for_validation_is_invalid(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.DATE.name,
            'validation': 'gte pfdvnbosarepwfodn'
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == parameter_errors[
            'invalid_date'].format('pfdvnbosarepwfodn')

    def test_should_throw_error_when_value_type_is_date_time_and_validation_value_is_number(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.DATE_TIME.name,
            'validation': 'gte 5001'
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == parameter_errors[
            'number_not_a_date'].format('DATE_TIME', 'gte 5001')

    def test_when_validation_type_is_enum_then_validation_must_be_provided(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.ENUM.name
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == parameter_errors[
            'missing_validation_for_type'].format('ENUM')

    def test_when_validation_type_is_enum_then_values_must_be_more_than_1(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'V1',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.ENUM.name,
            'validation': 'Completed'
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == parameter_errors[
            'enum_has_one_field']

    def test_validation_should_be_comma_seperated_words_when_type_is_enum(
            self, app, init_db, client, saved_org_and_user_generator,
            bulk_create_unit_objects):
        run_test_precondition()
        user, org = saved_org_and_user_generator
        unit = Unit.query.filter_by(name='Voltage').first()
        parameter_json = {
            'name': 'Status',
            'unitId': unit.id,
            'valueType': ValueTypeEnum.ENUM.name,
            'validation': 'Completed, Pending, Working'
        }
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
        response = client.post(PARAMETER_ENDPOINTS.format(org.id),
                               data=json.dumps(parameter_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 201
        assert response_body['message'] == CREATED.format('Parameter')
        assert response_body['data']['name'] == parameter_json['name']
        assert response_body['data']['unit']['id'] == parameter_json['unitId']
        assert response_body['data']['createdAt'] is not None
        assert response_body['message'] == CREATED.format('Parameter')
        assert response_body['data']['editable'] is True
        assert response_body['data'][
            'validation'] == 'Completed,Pending,Working'


class TestRetrieveParameter:
    def test_user_should_be_retrieved(self, init_db, client,
                                      saved_parameters_to_org):
        run_test_precondition()
        params_objs, org = saved_parameters_to_org(5)
        token = UserGenerator.generate_token(org.creator)
        url = PARAMETER_ENDPOINTS.format(org.id)

        response_body = assert_paginator_data_values(
            user=org.creator,
            created_objs=params_objs,
            client=client,
            token=token,
            url=f'{url}',
            success_msg=RETRIEVED.format('Parameter'),
            current_page=1,
            total_objects=5,
            next_page=None,
            prev_page=None,
        )
        for data in response_body['data']:
            assert data['unit'] is None

    def test_should_retrieve_units_when_the_parameter_has_a_unit(
            self, init_db, client, saved_parameters_to_org):
        run_test_precondition()
        unit = Unit.query.filter_by(name='Voltage').first()
        params_objs, org = saved_parameters_to_org(5, unit_id=unit.id)
        token = UserGenerator.generate_token(org.creator)
        url = PARAMETER_ENDPOINTS.format(org.id)

        response_body = assert_paginator_data_values(
            user=org.creator,
            created_objs=params_objs,
            client=client,
            token=token,
            url=f'{url}',
            success_msg=RETRIEVED.format('Parameter'),
            current_page=1,
            total_objects=5,
            next_page=None,
            prev_page=None,
        )
        for data in response_body['data']:
            assert data['unit']['id'] == unit.id
            assert data['unit']['name'] == 'Voltage'

    def test_should_be_able_to_search_for_specific_parameter(
            self, init_db, client, saved_parameters_to_org):
        run_test_precondition()
        unit = Unit.query.filter_by(name='Voltage').first()
        params_objs, org = saved_parameters_to_org(10, unit_id=unit.id)
        token = UserGenerator.generate_token(org.creator)
        url = PARAMETER_ENDPOINTS.format(org.id)
        assert Parameter.query.count() == 10
        response_body = assert_paginator_data_values(
            user=org.creator,
            created_objs=params_objs,
            client=client,
            token=token,
            url=f'{url}?name_search={params_objs[0].name}',
            success_msg=RETRIEVED.format('Parameter'),
            current_page=1,
            total_objects=1,
            next_page=None,
            prev_page=None,
        )
        assert len(response_body['data']) == 1
